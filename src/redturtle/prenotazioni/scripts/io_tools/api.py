# -*- coding: utf-8 -*-
"""
A message is conceptually very similar to an email and, in its simplest form, is composed of the following attributes:

    A required subject: a short description of the topic.
    A required markdown body: a Markdown representation of the body (see below on what Markdown tags are allowed).
    An optional payment_data: in case the message is a payment request, the payment data will enable the recipient to pay the requested amount via PagoPA.
    An optional due_date: a due date that let the recipient add a reminder when receiving the message. The format for all dates is ISO8601 with time information and UTC timezone (ie. "2018-10-13T00:00:00.000Z").

"""
from datetime import datetime

# from pkg_resources import resource_filename
# from bravado.swagger_model import load_file
from bravado.client import SwaggerClient
from bravado.exception import HTTPForbidden
from bravado.requests_client import RequestsClient
from pytz import timezone

from . import logger

# STATUS INTERNI A QUESTA API
PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
QUEUED = "QUEUED"
ERROR = "ERROR"
SENDER_NOT_ALLOWED = "SENDER_NOT_ALLOWED"

# STATUS tornati da PagoPA:

# The processing status of a message. "ACCEPTED": the message has
# been accepted and will be processed for delivery; we'll try to store
# its content in the user's inbox and notify him on his preferred channels
# "THROTTLED": a temporary failure caused a retry during the message processing;
# any notification associated with this message will be delayed for a maximum of 7 days
# "FAILED": a permanent failure caused the process to exit with an error, no notification
# will be sent for this message "PROCESSED": the message was succesfully processed and is
# now stored in the user's inbox; we'll try to send a notification for each of the selected
# channels "REJECTED": either the recipient does not exist, or the sender has been blocked
PROCESSED = "PROCESSED"
REJECTED = "REJECTED"
FAILED = "FAILED"

PERMANENT_STATUS = (PROCESSED, REJECTED, FAILED)


class Api(object):
    def __init__(self, secret, storage=None):
        self.storage = storage
        header = "Ocp-Apim-Subscription-Key"
        http_client = RequestsClient()
        http_client.set_api_key(
            "api.io.italia.it", secret, param_name=header, param_in="header"
        )
        # TODO: cache delle specifiche openapi
        self.api = SwaggerClient.from_url(
            "https://raw.githubusercontent.com/teamdigitale/io-functions-services/master/openapi/index.yaml",
            http_client=http_client,
        )
        # api = SwaggerClient.from_spec(
        #     load_file(resource_filename('io_tools', 'spec.yaml')),
        #     http_client=http_client,
        # )

    def update_message_status(
        self,
        key,
    ):
        """[summary]

        Args:
            key ([type]): [description]
        """
        msg = self.storage.get_message(key=key)
        if msg and msg.status not in PERMANENT_STATUS:
            fiscal_code = msg.fiscal_code
            msgid = msg.msgid
            res = self.api.messages.getMessage(
                fiscal_code=fiscal_code, id=msgid
            )._get_incoming_response()
            if res.status_code == 200:
                self.storage.update_message(key, **res.json())
                return True
            else:
                logger.warning(
                    "unable to get message %s %s - %s",
                    fiscal_code,
                    msgid,
                    res.status_code,
                )
                return False
        return False

    def send_message(
        self, fiscal_code, subject, body, payment_data=None, due_date=None, key=None
    ):
        """[summary]

        Args:
            fiscal_code ([type]): [description]
            subject ([type]): [description]
            body ([type]): [description]
            payment_data ([dict], optional): ... Defaults to None.
            due_date ([datetime], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        # 0. validazione argomenti
        if len(subject) < 10 or len(subject) > 120:
            logger.error(
                "la lunghezza dell'oggetto del messaggio deve stare tra i 10 e i 120 caratteri"
            )
            return None
        if len(body) < 80 or len(body) > 10000:
            logger.error(
                "la lunghezza del contenuto del messaggio deve stare tra i 80 e i 10.000 caratteri"
            )
            return None
        if due_date and not isinstance(due_date, datetime):
            logger.error(
                "il campo con la data, se valorizzato, deve essere di tipo datetime"
            )
            return None
        if key is None:
            if payment_data:
                key = "#".join([fiscal_code, subject, payment_data["notice_number"]])
            else:
                key = payment_data or "#".join([fiscal_code, subject])
        # 1. verifica che lo stesso messaggio non sia già stato mandato
        msg = self.storage.get_message(key=key)
        if msg:
            if msg.status != PROFILE_NOT_FOUND:
                logger.warning("message %r already managed", msg)
                # TODO: verificare come/se gestire eventuali messaggi non correttamente inviati
                # Aggiunta verifica su profilo inesistente, il destinatario potrebbe aver attivato il profilo su app IO, in questo caso il messaggio cambia stato e viene spedito
                return msg.msgid
        else:
            msg = self.storage.create_message(
                key, fiscal_code, subject, body, payment_data, due_date
            )
        # 2. verifica se il destinatario è abilitato o meno a ricevere il messaggio
        try:
            profile = (
                self.api.profiles.getProfile(fiscal_code=fiscal_code).response().result
            )
        except HTTPForbidden:
            self.storage.update_message(key, status=PROFILE_NOT_FOUND)
            logger.error(
                "profile for user %s not found (access forbidden to api)", fiscal_code
            )
            return None
        except Exception:
            self.storage.update_message(key, status=PROFILE_NOT_FOUND)
            logger.exception(
                "profile for user %s not found (generic error)", fiscal_code
            )
            return None
        if profile and profile.sender_allowed:
            # PaymentData non definito nello swagger, payment_data come dizionario
            # è comunque sufficiente
            # if payment_data:
            #     payment_data = self.api.get_model('PaymentData')(
            #         **payment_data
            #     )
            if isinstance(due_date, datetime):
                # https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python
                # due_date = due_date.astimezone().isoformat()
                due_date = due_date.astimezone(timezone("utc")).strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z"
                )
            message = self.api.get_model("NewMessage")(
                # time_to_live
                # default_addresses=None
                subject=subject,
                content=self.api.get_model("MessageContent")(
                    subject=subject,
                    markdown=body,
                    payment_data=payment_data,
                    # prescription_data
                    due_date=due_date,
                ),
            )
            resp = self.api.messages.submitMessageforUser(
                fiscal_code=fiscal_code,
                message=message,
            )._get_incoming_response()
            if resp.status_code == 201:
                data = resp.json()
                msgid = data["id"]
                self.storage.update_message(key, msgid=msgid, status=QUEUED)
                logger.info(
                    "message %s queued for %s (msgid %s)", subject, fiscal_code, msgid
                )
                return msgid
            else:
                self.storage.update_message(key, info=resp.text, status=ERROR)
                logger.error(
                    "error sending message %s to %s - %s - %s",
                    subject,
                    fiscal_code,
                    resp.status_code,
                    resp.text,
                )
                return None
        else:
            self.storage.update_message(key, status=SENDER_NOT_ALLOWED)
            logger.warning("message for user %s not allowed", fiscal_code)
            return None

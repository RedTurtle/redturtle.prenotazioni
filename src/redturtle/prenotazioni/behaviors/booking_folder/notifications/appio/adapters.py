# -*- coding: utf-8 -*-
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.behaviors.booking_folder.notifications.appio.voc_service_keys import (
    API_KEYS,
)
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingAPPIoMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.io_tools.api import Api
from redturtle.prenotazioni.io_tools.storage import logstorage
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory

import os


APPIO_DUMMY_CF = os.getenv("APPIO_DUMMY_CF")


@implementer(IBookingNotificationSender)
@adapter(IBookingAPPIoMessage, IPrenotazione, IRedturtlePrenotazioniLayer)
class BookingTransitionAPPIoSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def get_api(self, api_key, storage=logstorage):
        return Api(secret=api_key, storage=storage)

    def send(self) -> bool:
        from .. import write_message_to_object_history

        supervisor = getUtility(IBookingNotificatorSupervisorUtility)

        if supervisor.is_appio_message_allowed(self.booking):
            message = self.message_adapter.message
            subject = self.message_adapter.subject
            booking_type = self.booking.get_booking_type()
            service_code = getattr(booking_type, "service_code", None)

            if not self.booking.fiscalcode:
                logger.warning(
                    "No fiscal code found for booking %s", self.booking.UID()
                )
                return False

            if not service_code:
                logger.warning(
                    "No App IO service code found for booking type %s", booking_type
                )
                return False

            term = getUtility(
                IVocabularyFactory, "redturtle.prenotazioni.appio_services"
            )(self.booking).getTerm(service_code)

            if term and term.value in API_KEYS:
                api_key = API_KEYS[term.value]
            elif term:
                # backward compatibility
                api_key = term.value
            else:
                api_key = None

            if not api_key:
                logger.warning(
                    "No App IO API key found for service code %s booking type %s",
                    service_code,
                    booking_type,
                )
                return False

            appio_api = self.get_api(api_key)

            if not appio_api:
                logger.error("appio api unavailable")
                return False

            fiscalcode = self.booking.fiscalcode
            # XXX: debug
            if APPIO_DUMMY_CF:
                fiscalcode = "AAAAAA00A00A000A"

            fiscalcode = fiscalcode.upper()
            if fiscalcode.startswith("TINIT-"):
                fiscalcode = fiscalcode[6:]

            if not appio_api.is_service_activated(fiscalcode):
                logger.info(
                    "App IO service %s is not activated for fiscal code %s",
                    service_code,
                    fiscalcode,
                )
                return False

            msgid = appio_api.send_message(
                fiscal_code=fiscalcode,
                subject=subject,
                body=message,
                trim_text=True,
            )

            if not msgid:
                logger.error("Could not send notification via AppIO gateway")
                return False

            logger.info(
                "Sent the notification <%s>(`%s`) via AppIO gateway, id returned: %s",
                self.booking.UID(),
                subject,
                msgid,
            )

            write_message_to_object_history(
                self.booking, self.message_adapter.message_history
            )

            return True

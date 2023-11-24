# -*- encoding: utf-8 -*-
import locale
import logging
import sys
from datetime import datetime
from datetime import timedelta

import click
import transaction
from plone import api
from zope.annotation.interfaces import IAnnotations

from redturtle.prenotazioni.config import NOTIFICATIONS_LOGS
from redturtle.prenotazioni.config import VERIFIED_BOOKING

from .io_tools.api import Api
from .io_tools.storage import logstorage

logger = logging.getLogger("redturtle.prenotazioni.app_io")
locale.setlocale(locale.LC_ALL, "it_IT.UTF-8")


def days_before(obj, days=1, as_date=True):
    if as_date:
        if (
            timedelta()
            < obj.booking_date.date() - datetime.now().date()
            <= timedelta(days=days)
        ):
            return True
    else:
        if timedelta() < obj.booking_date - datetime.now() <= timedelta(days=days):
            return True
    return False


MSGS = {
    "1day": """
Il Comune le ricorda il suo appuntamento di domani {day}
alle ore {time} presso {how_to_get_here}{sportello}.
{booking_code}"""
}


def notifica_app_io(obj, api_io, msg_type, commit=False, verbose=False):
    annotations = IAnnotations(obj)
    fiscal_code = obj.fiscalcode
    if not annotations.get(VERIFIED_BOOKING):
        logger.info(
            "Prenotazione %s non verificata per invio notifiche App IO",
            obj.absolute_url(),
        )
        return False
    if fiscal_code:
        # TODO: spostare i template di messaggi in una configurazione esterna
        # allo script
        # TODO: esistono definite delle stringiterp plone, valutare se usare quelle
        subject = "Promemoria appuntamento"
        folder = obj.getPrenotazioniFolder()
        how_to_get_here = getattr(folder, "how_to_get_here", None) or ""
        # how_to_get_here = getattr(folder, "how_to_get_here", "")
        # BODY: markdown, 'maxLength': 10000, 'minLength': 80
        body = (MSGS[msg_type]).format(
            day=obj.booking_date.strftime("%d %B %Y"),
            time=obj.booking_date.strftime("%H:%M"),
            how_to_get_here=how_to_get_here,
            # sportello=u" sportello %s" % obj.gate if obj.gate else "",
            sportello=" - %s" % obj.gate if obj.gate else "",
            booking_code="\n\nIl codice della prenotazione è %s" % obj.getBookingCode()
            if obj.getBookingCode()
            else "",
        )
        key = "%s_%s" % (obj.UID(), msg_type)
        msg = api_io.storage.get_message(key=key)
        if msg and msg.msgid:
            logger.info("Notifica precedentemente inviata %s", msg)
            return api_io.update_message_status(key=key)
        elif commit:
            msgid = api_io.send_message(
                fiscal_code=fiscal_code,
                subject=subject,
                body=body,
                key=key,
            )
            logger.info("Notifica %s per %s - %s", msgid, fiscal_code, subject)
            return bool(msgid)
        else:
            logger.warning(
                "<DEBUG> TO:%s SUBJECT:%s BODY:%s, KEY:%s",
                fiscal_code,
                subject,
                body,
                key,
            )
            return True
    else:
        logger.info(
            "prenotazione %s fiscal_code=%s non presente",
            obj.absolute_url(),
            fiscal_code,
        )
        return False


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    def __repr__(self):
        return self.__dict__.__repr__()


class Storage(object):
    def __init__(self, context):
        self.context = IAnnotations(context)

    def get_message(self, key):
        d = self.context.get("%s.%s" % (NOTIFICATIONS_LOGS, key))
        return ObjectView(d) if d else None

    def create_message(self, key, fiscal_code, subject, body, payment_data, due_date):
        msg = {
            "key": key,
            "fiscal_code": fiscal_code,
            "subject": subject,
            "body": body,
            # "payment_data": payment_data,
            # "due_data": due_data,
        }
        self.context["%s.%s" % (NOTIFICATIONS_LOGS, key)] = msg
        return ObjectView(msg)

    def update_message(self, key, **kwargs):
        msg = self.context.get("%s.%s" % (NOTIFICATIONS_LOGS, key)) or {}
        # update o sostituzione completa ?
        msg.update(kwargs)
        self.context["%s.%s" % (NOTIFICATIONS_LOGS, key)] = msg

    def cleanup(self):
        ids = [k for k in self.context if k.startswith(NOTIFICATIONS_LOGS)]
        for id in ids:
            del self.context[id]


@click.command()
@click.option("--commit/--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, help="Will print verbose messages.")
@click.option("--io-secret")
@click.option("--test-message", is_flag=True, default=False)
@click.option("--test-message-cf")
def _main(commit, verbose, io_secret, test_message, test_message_cf):
    if verbose:
        logging.getLogger().setLevel(logging.INFO)

    if commit and not io_secret:
        print("Missing --io-secret")  # NOQA
        return -1

    api_io = Api(secret=io_secret)

    if test_message and test_message_cf:
        if not io_secret:
            print("Missing --io-secret")  # NOQA
            return -1
        api_io.storage = logstorage
        msgid = api_io.send_message(
            fiscal_code=test_message_cf,
            subject="Messaggio di prova",
            body="0123456789 " * 9,
        )
        return bool(msgid)

    catalog = api.portal.get_tool("portal_catalog")

    # TODO: spostare la configurazione in un file fuori dallo script
    actions = (
        (
            days_before,
            {"days": 1, "as_date": True},
            notifica_app_io,
            {
                "api_io": api_io,
                "msg_type": "1day",
                "commit": commit,
                "verbose": verbose,
            },
        ),
    )

    # XXX: valutare un filtro più preciso sulle ricerche e degli indici/metadati sul catalogo
    for brain in catalog.unrestrictedSearchResults(
        portal_type="Prenotazione", review_state="confirmed"
    ):
        obj = brain.getObject()
        if not obj.app_io_enabled:
            logger.info("App IO reminder disabled for %s", brain.getPath())
            continue
        api_io.storage = Storage(obj)
        # api_io.storage.cleanup()
        for action in actions:
            if action[0](obj, **action[1]):
                if action[2](obj, **action[3]):
                    if commit:
                        logger.info("COMMIT")
                        transaction.commit()

    # if commit:
    #     transaction.commit()
    #     logger.warning('Changes Saved')
    # else:
    #     transaction.abort()
    #     logger.warning('Dry Run mode - nothing changed')


def main():
    if "-c" in sys.argv:
        _main(sys.argv[3:])
    else:
        _main()


if __name__ == "__main__":
    main()

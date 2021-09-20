# -*- encoding: utf-8 -*-
import click
from datetime import datetime
from datetime import timedelta
import logging
from plone import api
from redturtle.prenotazioni.config import NOTIFICATIONS_LOGS
from redturtle.prenotazioni.config import VERIFIED_BOOKING
import sys
import transaction
from zope.annotation.interfaces import IAnnotations

from .io_tools.api import Api


logger = logging.getLogger('redturtle.prenotazioni.app_io')


def days_before(obj, days=1):
    if timedelta() < obj.data_prenotazione - datetime.now() < timedelta(days=days):
        return True
    return False


def notifica_app_io(obj, api_io, msg_type, commit=False, verbose=False):
    annotations = IAnnotations(obj)
    fiscal_code = obj.fiscalcode
    if not annotations.get(VERIFIED_BOOKING):
        logger.info(
            "Prenotazione %s non verificata per invio notifiche App IO",
            obj.absolute_url())
        return False
    if fiscal_code:
        subject = "%s %s" % (obj.Title(), msg_type)
        # BODY: markdown, 'maxLength': 10000, 'minLength': 80
        body = "##%s\n" % msg_type + ("* TODO\n" * 20)
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
            logger.warning("<DEBUG> TO:%s SUBJECT:%s BODY:%s, KEY:%s",
                           fiscal_code, subject, body, key)
            return True
    else:
        logger.info("prenotazione %s fiscal_code=%s non presente",
                    obj.absolute_url(), fiscal_code)
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
@click.option('--commit/--dry-run', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--io-secret')
def _main(commit, verbose, io_secret):

    if verbose:
        logging.getLogger().setLevel(logging.INFO)

    if commit and not io_secret:
        print("Missing --io-secret")  # NOQA
        return -1

    catalog = api.portal.get_tool('portal_catalog')
    api_io = Api(secret=io_secret)

    actions = (
        (
            days_before, {"days": 5},
            notifica_app_io, {
                "api_io": api_io,
                "msg_type": "5days",
                "commit": commit,
                "verbose": verbose
            },
        ),
    )

    # XXX: valutare un filtro più preciso sulle ricerche e degli indici/metadati sul catalogo
    for brain in catalog.unrestrictedSearchResults(portal_type="Prenotazione", review_state="published"):
        obj = brain.getObject()
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
    if '-c' in sys.argv:
        _main(sys.argv[3:])
    else:
        _main()


if __name__ == "__main__":
    main()

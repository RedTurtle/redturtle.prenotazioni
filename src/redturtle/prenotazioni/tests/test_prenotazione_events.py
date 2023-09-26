# -*- coding: UTF-8 -*-
import email
import unittest
from datetime import date, datetime, timedelta

import pytz
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from zope.event import notify
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.prenotazione_event import MovedPrenotazione
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestSPrenotazioneEvents(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    maxDiff = None
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        self.email_subject = "Testing subject"
        self.email_message = "Testing message"

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
        )
        self.today_8_0 = self.dt_local_to_utc(
            datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        )
        self.tomorrow_8_0 = self.today_8_0 + timedelta(1)
        week_table = self.folder_prenotazioni.week_table
        for data in week_table:
            data["morning_start"] = "0700"
            data["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        api.portal.set_registry_record(
            "plone.portal_timezone",
            self.timezone,
        )

    def create_booking(self, booking_date=None):
        booker = IBooker(self.folder_prenotazioni)
        if booking_date is None:
            booking_date = self.tomorrow_8_0
        return booker.create(
            {
                "booking_date": booking_date,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

    def test_email_sent_on_submit(self):
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_submit_subject = self.email_subject
        self.folder_prenotazioni.notify_on_submit_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            self.email_subject,
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            self.email_message,
            mail.get_payload()[0].get_payload(),
        )

    def test_email_send_on_confirm(self):
        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_confirm_subject = self.email_subject
        self.folder_prenotazioni.notify_on_confirm_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        booking = self.create_booking()

        api.content.transition(booking, "confirm")

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            self.email_subject,
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            self.email_message,
            mail.get_payload()[0].get_payload(),
        )

    def test_email_send_on_reject(self):
        self.folder_prenotazioni.notify_on_refuse = True
        self.folder_prenotazioni.notify_on_refuse_subject = self.email_subject
        self.folder_prenotazioni.notify_on_refuse_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        booking = self.create_booking()

        api.content.transition(booking, "refuse")

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            self.email_subject,
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            self.email_message,
            mail.get_payload()[0].get_payload(),
        )

    def test_email_not_sent_on_submit_if_on_confirm_true(self):
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_confirm_subject = self.email_subject
        self.folder_prenotazioni.notify_on_confirm_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        booking = self.create_booking()

        api.content.transition(booking, "confirm")

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            self.email_subject,
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            self.email_message,
            mail.get_payload()[0].get_payload(),
        )

    def test_email_send_on_prenotazione_move(self):
        self.folder_prenotazioni.notify_on_move = True
        self.folder_prenotazioni.notify_on_move_subject = self.email_subject
        self.folder_prenotazioni.notify_on_move_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        notify(MovedPrenotazione(self.create_booking()))

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            self.email_subject,
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            self.email_message,
            mail.get_payload()[0].get_payload(),
        )

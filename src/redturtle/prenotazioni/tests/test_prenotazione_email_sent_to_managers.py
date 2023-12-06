# -*- coding: UTF-8 -*-
import email
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestEmailToManagers(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        week_table = self.folder_prenotazioni.week_table
        for data in week_table:
            data["morning_start"] = "0700"
            data["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        self.today_8_0 = self.dt_local_to_utc(
            datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        )
        self.tomorrow_8_0 = self.today_8_0 + timedelta(1)
        self.folder_prenotazioni.email_responsabile = ["admin@test.com"]
        api.portal.set_registry_record(
            "plone.portal_timezone",
            self.timezone,
        )

    def create_booking(self):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(
            {
                "booking_date": self.tomorrow_8_0,  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

    def test_email_sent_to_managers_on_creation(self):
        self.assertFalse(self.mailhost.messages)

        self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            "New booking for Prenota foo",
            "".join([i for i in mail.values()]),
        )
        self.assertIn(
            "Go to the booking to see more details and manage it",
            mail.get_payload()[0].get_payload(),
        )

    def test_email_sent_to_managers_has_ical(self):
        self.assertFalse(self.mailhost.messages)

        self.assertFalse(self.mailhost.messages)
        booking = self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail_sent = self.mailhost.messages[0]
        message = email.message_from_bytes(mail_sent)

        self.assertTrue(len(message.get_payload()), 2)

        attachment = message.get_payload()[1]
        data = attachment.get_payload()

        self.assertTrue(message.is_multipart())
        self.assertIn(
            f"SUMMARY:Booking for foo [{self.folder_prenotazioni.title}]", data
        )
        if api.env.plone_version() < "6":
            self.assertIn(
                f'DTSTART;VALUE=DATE-TIME:{booking.booking_date.strftime("%Y%m%dT%H%M%S")}',
                data,
            )
            self.assertIn(
                f'DTEND;VALUE=DATE-TIME:{booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")}',
                data,
            )
        else:
            self.assertIn(
                f'DTSTART:{booking.booking_date.strftime("%Y%m%dT%H%M%S")}',
                data,
            )
            self.assertIn(
                f'DTEND:{booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")}',
                data,
            )
        self.assertIn(f"UID:{booking.UID()}", data)

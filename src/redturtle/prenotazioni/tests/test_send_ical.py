# -*- coding: UTF-8 -*-
# TODO: Evaluate if we can join the prenotazioni event tests with the tests below so
# as now the ical is being added in the templates adaptes used py plone event
import base64
import email
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

from collective.contentrules.mailfromfield.actions.mail import MailFromFieldAction
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.contentrules.rule.interfaces import IExecutable
from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.prenotazione_event import MovedPrenotazione
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestSendIcal(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

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
            week_table=[
                {
                    "day": "Lunedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Martedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Mercoledì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Giovedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Venerdì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Sabato",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Domenica",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            gates=["Gate A"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        self.today = datetime.now().replace(hour=8)
        self.tomorrow = self.today + timedelta(1)

    def create_booking(self):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(
            {
                "booking_date": self.tomorrow,  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

    def test_ical_sent_on_confirm(self):
        booking = self.create_booking()
        e = MailFromFieldAction()
        e.source = "foo@bar.be"
        e.fieldName = "email"
        e.target = "target"
        e.message = "Test mail"
        e.subject = "Subject"
        ex = getMultiAdapter(
            (
                self.portal,
                e,
                ActionSucceededEvent(
                    object=booking,
                    workflow=None,
                    action="confirm",
                    result="",
                ),
            ),
            IExecutable,
        )
        ex()
        mailSent = self.mailhost.messages[0]
        message = email.message_from_bytes(mailSent)

        self.assertTrue(len(message.get_payload()), 2)

        attachment = message.get_payload()[1]
        data = base64.b64decode(attachment.get_payload()).decode("utf-8")

        self.assertTrue(message.is_multipart())
        self.assertEqual(attachment.get_filename(), "foo.ics")
        self.assertIn("SUMMARY:Booking for Prenota foo", data)
        if api.env.plone_version() < "6":
            self.assertIn(
                "DTSTART;VALUE=DATE-TIME:{}".format(
                    booking.booking_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
            self.assertIn(
                "DTEND;VALUE=DATE-TIME:{}".format(
                    booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
        else:
            self.assertIn(
                "DTSTART:{}".format(booking.booking_date.strftime("%Y%m%dT%H%M%S")),
                data,
            )
            self.assertIn(
                "DTEND:{}".format(
                    booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
        self.assertIn("UID:{}".format(booking.UID()), data)

    def test_ical_not_sent_on_refuse(self):
        booking = self.create_booking()
        e = MailFromFieldAction()
        e.source = "foo@bar.be"
        e.fieldName = "email"
        e.target = "target"
        e.message = "Test mail"
        e.subject = "Subject"
        ex = getMultiAdapter(
            (
                self.portal,
                e,
                ActionSucceededEvent(
                    object=booking,
                    workflow=None,
                    action="refuse",
                    result="",
                ),
            ),
            IExecutable,
        )
        ex()
        mailSent = self.mailhost.messages[0]
        message = email.message_from_bytes(mailSent)

        self.assertFalse(message.is_multipart())
        self.assertEqual(message.get_payload(), "Test mail\n")

    def test_ical_not_sent_on_submit(self):
        booking = self.create_booking()
        e = MailFromFieldAction()
        e.source = "foo@bar.be"
        e.fieldName = "email"
        e.target = "target"
        e.message = "Test mail"
        e.subject = "Subject"
        ex = getMultiAdapter(
            (
                self.portal,
                e,
                ActionSucceededEvent(
                    object=booking,
                    workflow=None,
                    action="submit",
                    result="",
                ),
            ),
            IExecutable,
        )
        ex()
        mailSent = self.mailhost.messages[0]
        message = email.message_from_bytes(mailSent)

        self.assertFalse(message.is_multipart())
        self.assertEqual(message.get_payload(), "Test mail\n")

    def test_ical_sent_on_move(self):
        booking = self.create_booking()

        # move date one day after
        booking.booking_date = booking.booking_date + timedelta(1)
        booking.booking_expiration_date = booking.booking_expiration_date + timedelta(1)

        e = MailFromFieldAction()
        e.source = "foo@bar.be"
        e.fieldName = "email"
        e.target = "target"
        e.message = "Test mail"
        e.subject = "Subject"
        ex = getMultiAdapter(
            (
                self.portal,
                e,
                MovedPrenotazione(
                    obj=booking,
                ),
            ),
            IExecutable,
        )
        ex()
        mailSent = self.mailhost.messages[0]
        message = email.message_from_bytes(mailSent)

        self.assertTrue(len(message.get_payload()), 2)

        attachment = message.get_payload()[1]
        data = base64.b64decode(attachment.get_payload()).decode("utf-8")

        self.assertTrue(message.is_multipart())
        self.assertEqual(attachment.get_filename(), "foo.ics")
        self.assertIn("SUMMARY:Booking for Prenota foo", data)
        if api.env.plone_version() < "6":
            self.assertIn(
                "DTSTART;VALUE=DATE-TIME:{}".format(
                    booking.booking_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
            self.assertIn(
                "DTEND;VALUE=DATE-TIME:{}".format(
                    booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
        else:
            self.assertIn(
                "DTSTART:{}".format(booking.booking_date.strftime("%Y%m%dT%H%M%S")),
                data,
            )
            self.assertIn(
                "DTEND:{}".format(
                    booking.booking_expiration_date.strftime("%Y%m%dT%H%M%S")
                ),
                data,
            )
        self.assertIn("UID:{}".format(booking.UID()), data)

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
            gates=["Gate A"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
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

    def test_email_send_on_submit_and_confirm_if_not_autoconfirm(self):
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_submit_subject = (
            f"{self.email_subject} on submit"
        )
        self.folder_prenotazioni.notify_on_submit_message = (
            f"{self.email_message} on submit"
        )
        self.folder_prenotazioni.notify_on_confirm_subject = (
            f"{self.email_subject} on confirm"
        )
        self.folder_prenotazioni.notify_on_confirm_message = (
            f"{self.email_message} on confirm"
        )

        self.assertFalse(self.mailhost.messages)

        booking = self.create_booking()

        api.content.transition(booking, "confirm")

        self.assertEqual(len(self.mailhost.messages), 2)

        submit_mail = email.message_from_bytes(self.mailhost.messages[0])
        confirm_mail = email.message_from_bytes(self.mailhost.messages[1])

        self.assertIn(
            f"{self.email_subject} on submit",
            "".join([i for i in submit_mail.values()]),
        )
        self.assertIn(
            f"{self.email_subject} on confirm",
            "".join([i for i in confirm_mail.values()]),
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

    def test_email_not_sent_on_submit_if_on_confirm_true_and_autoconfirm(self):
        self.folder_prenotazioni.auto_confirm = True
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_submit_subject = (
            f"{self.email_subject} on submit"
        )
        self.folder_prenotazioni.notify_on_submit_message = (
            f"{self.email_message} on submit"
        )
        self.folder_prenotazioni.notify_on_confirm_subject = (
            f"{self.email_subject} on confirm"
        )
        self.folder_prenotazioni.notify_on_confirm_message = (
            f"{self.email_message} on confirm"
        )

        self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            f"{self.email_subject} on confirm",
            "".join([i for i in mail.values()]),
        )

    def test_email_sent_on_submit_if_autoconfirm_and_not_on_confirm(self):
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_confirm = False
        self.folder_prenotazioni.notify_on_submit_subject = (
            f"{self.email_subject} on submit"
        )
        self.folder_prenotazioni.notify_on_submit_message = (
            f"{self.email_message} on submit"
        )
        self.folder_prenotazioni.notify_on_confirm_subject = (
            f"{self.email_subject} on confirm"
        )
        self.folder_prenotazioni.notify_on_confirm_message = (
            f"{self.email_message} on confirm"
        )
        self.folder_prenotazioni.auto_confirm = True

        self.assertFalse(self.mailhost.messages)

        self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail = email.message_from_bytes(self.mailhost.messages[0])

        self.assertTrue(mail.is_multipart())

        self.assertIn(
            f"{self.email_subject} on submit",
            "".join([i for i in mail.values()]),
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

    def test_email_send_on_prenotazione_move_has_ical(self):
        self.folder_prenotazioni.notify_on_move = True
        self.folder_prenotazioni.notify_on_move_subject = self.email_subject
        self.folder_prenotazioni.notify_on_move_message = self.email_message

        self.assertFalse(self.mailhost.messages)
        booking = self.create_booking()
        notify(MovedPrenotazione(booking))

        self.assertEqual(len(self.mailhost.messages), 1)

        mail_sent = self.mailhost.messages[0]
        message = email.message_from_bytes(mail_sent)

        self.assertTrue(len(message.get_payload()), 2)

        attachment = message.get_payload()[1]
        data = attachment.get_payload()

        self.assertTrue(message.is_multipart())
        self.assertEqual(attachment.get_filename(), "foo.ics")
        self.assertIn("SUMMARY:Booking for Prenota foo", data)
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

    def test_email_send_on_submit_does_not_have_ical(self):
        self.folder_prenotazioni.notify_on_submit = True
        self.folder_prenotazioni.notify_on_submit_subject = self.email_subject
        self.folder_prenotazioni.notify_on_submit_message = self.email_message

        self.assertFalse(self.mailhost.messages)
        self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail_sent = self.mailhost.messages[0]
        message = email.message_from_bytes(mail_sent)

        self.assertTrue(len(message.get_payload()), 1)

    def test_email_send_on_confirm_has_ical(self):
        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_confirm_subject = self.email_subject
        self.folder_prenotazioni.notify_on_confirm_message = self.email_message
        self.folder_prenotazioni.auto_confirm = True

        self.assertFalse(self.mailhost.messages)
        booking = self.create_booking()

        self.assertEqual(len(self.mailhost.messages), 1)

        mail_sent = self.mailhost.messages[0]
        message = email.message_from_bytes(mail_sent)

        self.assertTrue(len(message.get_payload()), 2)

        attachment = message.get_payload()[1]
        data = attachment.get_payload()

        self.assertTrue(message.is_multipart())
        self.assertEqual(attachment.get_filename(), "foo.ics")
        self.assertIn("SUMMARY:Booking for Prenota foo", data)
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

    def test_email_send_on_refuse_does_not_have_ical(self):
        self.folder_prenotazioni.notify_on_refuse = True
        self.folder_prenotazioni.notify_on_refuse_subject = self.email_subject
        self.folder_prenotazioni.notify_on_refuse_message = self.email_message

        self.assertFalse(self.mailhost.messages)
        booking = self.create_booking()
        api.content.transition(booking, "refuse")

        self.assertEqual(len(self.mailhost.messages), 1)

        mail_sent = self.mailhost.messages[0]
        message = email.message_from_bytes(mail_sent)

        self.assertTrue(len(message.get_payload()), 1)

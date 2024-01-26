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
from zope.component import getGlobalSiteManager
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.behaviors.booking_folder.notifications.sms.adapters import (
    BookingNotificationSender,
)
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingSMSMessage
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_API_INTEGRATION_TESTING,
)


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestBookingNotify(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_INTEGRATION_TESTING
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

        # Add SMS and AppIO behaviors to the PrenotazioniFolder
        portal_types = api.portal.get_tool("portal_types")
        content_type = portal_types["PrenotazioniFolder"]
        behaviors = list(content_type.behaviors)
        behaviors.append("redturtle.prenotazioni.behavior.notification_sms")
        content_type.behaviors = tuple(behaviors)

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

        self.sms = sms = []

        class CustomSMSSenderAdapter(BookingNotificationSender):
            def send(self):
                if self.is_notification_allowed():
                    # the message is automatically generated basing on the event type
                    message = self.message_adapter.message
                    phone = self.booking.phone
                    sms.append((phone, message))

        gsm = getGlobalSiteManager()
        gsm.registerAdapter(
            CustomSMSSenderAdapter,
            (IBookingSMSMessage, IPrenotazione, IRedturtlePrenotazioniLayer),
            IBookingNotificationSender,
            "booking_transition_sms_sender",
        )

    def create_booking(self, booking_date=None):
        booker = IBooker(self.folder_prenotazioni)
        return booker.book(
            {
                "booking_date": booking_date,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

    def test_sms_notification_on_create(self):
        self.folder_prenotazioni.notifications_sms_enabled = True
        self.folder_prenotazioni.notify_on_submit = True

        booker = IBooker(self.folder_prenotazioni)
        booking = booker.book(
            {
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "phone": "123456789",
            }
        )
        self.assertEqual(len(self.sms), 1)
        self.assertEqual(self.sms[0][0], "123456789")
        self.assertIn("[Prenota foo]: Booking Type A for ", self.sms[0][1])
        # default confirmation is not setted, so the sms is for creation
        self.assertIn(" at 08:00 has been created.", self.sms[0][1])

        # reject booking does not send sms
        api.content.transition(obj=booking, transition="refuse")
        self.assertEqual(len(self.sms), 1)

        self.folder_prenotazioni.notify_on_confirm = True
        api.content.transition(obj=booking, transition="restore")
        api.content.transition(obj=booking, transition="confirm")
        self.assertEqual(len(self.sms), 2)
        self.assertEqual(self.sms[-1][0], "123456789")
        self.assertIn("[Prenota foo]: Booking of ", self.sms[-1][1])
        self.assertIn(" at 08:00 has been accepted.", self.sms[-1][1])

        # now notify also refuse
        self.folder_prenotazioni.notify_on_refuse = True
        api.content.transition(obj=booking, transition="refuse")
        self.assertEqual(len(self.sms), 3)
        self.assertEqual(self.sms[-1][0], "123456789")
        self.assertIn("[Prenota foo]: The booking Type A of ", self.sms[-1][1])
        self.assertIn(" at 08:00 was refused.", self.sms[-1][1])

    def test_email_send_on_endpoint_call(self):
        self.booking = self.create_booking(booking_date=self.tomorrow_8_0)

        self.view = api.content.get_view(
            context=self.booking.getPrenotazioniFolder(),
            request=getRequest(),
            name="GET_application_json_@booking-notify",
        )
        self.view.booking_uid = self.booking.UID()

        self.folder_prenotazioni.notify_on_confirm = True
        self.folder_prenotazioni.notify_on_confirm_subject = self.email_subject
        self.folder_prenotazioni.notify_on_confirm_message = self.email_message

        self.assertFalse(self.mailhost.messages)

        self.view.reply()

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

# -*- coding: UTF-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.behaviors.booking_folder.notifications import (
    BookingNotificationSupervisorUtility,
)
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_API_INTEGRATION_TESTING,
)


class TestBookingNotificationSupervisorUtility(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_INTEGRATION_TESTING
    timezone = "Europe/Rome"

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        self.email_subject = "Testing subject"
        self.email_message = "Testing message"
        self.supervisor = BookingNotificationSupervisorUtility()

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

        self.booking = self.create_booking()

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def create_booking(self, booking_date=None):
        booker = IBooker(self.folder_prenotazioni)
        if booking_date is None:
            booking_date = self.tomorrow_8_0
        return booker.book(
            {
                "booking_date": booking_date,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": "FISCALCODE",
                "phone": "1111111111",
            }
        )

    def test_is_email_message_allowed_positive(self):
        self.folder_prenotazioni.notifications_email_enabled = True

        self.assertTrue(self.supervisor.is_email_message_allowed(self.booking))

    def test_is_email_message_allowed_positive_negative(self):
        self.folder_prenotazioni.notifications_email_enabled = False

        self.assertFalse(self.supervisor.is_email_message_allowed(self.booking))

        # No email provided

        self.folder_prenotazioni.notifications_email_enabled = True
        self.booking.email = None

        self.assertFalse(self.supervisor.is_appio_message_allowed(self.booking))

    def test_is_appio_message_allowed_positive(self):
        self.folder_prenotazioni.notifications_appio_enabled = True
        self.assertTrue(self.supervisor.is_appio_message_allowed(self.booking))

    def test_is_appio_message_allowed_negative(self):
        # Mock the AppIO subscription check
        self.supervisor._check_user_appio_subscription_to_booking_type = (
            lambda booking: True
        )

        self.folder_prenotazioni.notifications_appio_enabled = False

        self.assertFalse(self.supervisor.is_appio_message_allowed(self.booking))

        # No fiscalcode provided
        self.folder_prenotazioni.notifications_appio_enabled = True
        self.booking.fiscalcode = None

        self.assertFalse(self.supervisor.is_appio_message_allowed(self.booking))

    def test_is_sms_message_allowed_positive(self):
        self.supervisor.is_email_message_allowed = lambda booking: False
        self.supervisor.is_appio_message_allowed = lambda booking: False
        self.folder_prenotazioni.notifications_sms_enabled = True

        self.assertTrue(self.supervisor.is_sms_message_allowed(self.booking))

    def test_is_sms_message_allowed_negative(self):
        # Flag is False
        self.supervisor.is_email_message_allowed = lambda booking: True
        self.supervisor.is_appio_message_allowed = lambda booking: True
        self.folder_prenotazioni.notifications_sms_enabled = False

        self.assertFalse(self.supervisor.is_sms_message_allowed(self.booking))

        # No phone number was provided
        self.supervisor.is_email_message_allowed = lambda booking: True
        self.supervisor.is_appio_message_allowed = lambda booking: True
        self.folder_prenotazioni.notifications_sms_enabled = True

        self.booking.phone = None

        self.assertFalse(self.supervisor.is_sms_message_allowed(self.booking))

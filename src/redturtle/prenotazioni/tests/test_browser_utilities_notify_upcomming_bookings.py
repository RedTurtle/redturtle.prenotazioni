# -*- coding: UTF-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
from freezegun import freeze_time
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.component import adapter
from zope.component import provideHandler
from zope.globalrequest import getRequest

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

TESTING_TIME = datetime(year=2023, month=11, day=23, hour=12, minute=0)
NOTIFICAION_GAP = 3


class TestNotifyAboutUpcommingBookings(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    @freeze_time(TESTING_TIME)
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
            reminder_notification_gap=NOTIFICAION_GAP,
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )
        api.content.create(
            type="PrenotazioneType",
            title="Type B",
            duration=90,
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

    def create_booking(self, data: dict):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(data)

    @freeze_time(TESTING_TIME - timedelta(days=NOTIFICAION_GAP))
    def test_notification_event_is_raised_when_in_gap(self):
        events = []

        self.create_booking(
            data={
                "booking_date": TESTING_TIME,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

        @adapter(IBookingReminderEvent)
        def _handleReminder(_event):
            events.append(_event)

        provideHandler(_handleReminder)

        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

        self.assertTrue(IBookingReminderEvent.providedBy(events[0]))

    @freeze_time(TESTING_TIME - timedelta(days=NOTIFICAION_GAP - 1))
    def test_notification_event_is_not_raised_when_out_of_gap(self):
        events = []

        self.create_booking(
            data={
                "booking_date": TESTING_TIME,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

        @adapter(IBookingReminderEvent)
        def _handleReminder(_event):
            events.append(_event)

        provideHandler(_handleReminder)

        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

        self.assertEqual(len(events), 0)

    @freeze_time(TESTING_TIME - timedelta(days=NOTIFICAION_GAP))
    def test_notification_event_is_not_raised_when_gap_is_none(self):
        self.folder_prenotazioni.reminder_notification_gap = None
        events = []

        self.create_booking(
            data={
                "booking_date": TESTING_TIME,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

        @adapter(IBookingReminderEvent)
        def _handleReminder(_event):
            events.append(_event)

        provideHandler(_handleReminder)

        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

        self.assertEqual(len(events), 0)

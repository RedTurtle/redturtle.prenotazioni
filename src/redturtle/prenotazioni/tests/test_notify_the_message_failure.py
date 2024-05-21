# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta
from functools import partial

import pytz
import transaction
from plone import api
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.globalrequest import getRequest

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.behaviors.booking_folder.notifications import (
    notify_the_message_failure,
)
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


class TestNotifyTheMessageFailure(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    timezone = "Europe/Rome"

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )

        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A"],
            auto_confirm_manager=False,  # is True by default, but we are testing everything as manager
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
            }
        )

    def test_positive(self):
        booking = self.create_booking()
        event = object()

        class TestingException(Exception):
            pass

        decorator = partial(notify_the_message_failure, gateway_type="Gateway")

        @decorator
        def func(context, event):
            raise TestingException()

        self.assertRaises(TestingException, func, booking, event)

        transaction.commit()

        # Check if the error message was written to history
        self.assertIn(
            "Could not send Gateway message due to internal errors",
            [
                i["comments"]
                for i in ContentHistoryViewlet(
                    booking, getRequest(), None, None
                ).fullHistory()
            ],
        )

# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

from Acquisition import aq_parent
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


class TestPrenotazioniContextState(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )

        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])

        self.today = date.today()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=self.today,
            gates=["Gate A"],
            week_table=WEEK_TABLE_SCHEMA,
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")

        self.prenotazioni_context_state = api.content.get_view(
            context=self.folder_prenotazioni,
            request=self.request,
            name="prenotazioni_context_state",
        )

    def test_get_free_slots_skip_bookigs_inside_pause_range(self):
        booker = IBooker(self.folder_prenotazioni)

        today = date.today()
        # need this just to have the day container
        aq_parent(
            booker.book(
                {
                    "booking_date": datetime(
                        today.year, today.month, today.day, 10, 00
                    ),
                    "booking_type": "Type A",
                    "title": "foo",
                }
            )
        )

        self.folder_prenotazioni.pause_table = [
            {"day": "0", "pause_end": "1100", "pause_start": "0800"},
            {"day": "1", "pause_end": "1100", "pause_start": "0800"},
            {"day": "2", "pause_end": "1100", "pause_start": "0800"},
            {"day": "3", "pause_end": "1100", "pause_start": "0800"},
            {"day": "4", "pause_end": "1100", "pause_start": "0800"},
            {"day": "5", "pause_end": "1100", "pause_start": "0800"},
            {"day": "6", "pause_end": "1100", "pause_start": "0800"},
            {"day": "7", "pause_end": "1100", "pause_start": "0800"},
        ]

        res = self.prenotazioni_context_state.get_free_slots(today)
        # available slots are only arount the pause and not inside it
        self.assertEqual(len(res["Gate A"]), 2)
        self.assertEqual(
            self.prenotazioni_context_state.get_free_slots(today)["Gate A"][0].start(),
            "07:00",
        )
        self.assertEqual(
            self.prenotazioni_context_state.get_free_slots(today)["Gate A"][0].stop(),
            "08:00",
        )
        self.assertEqual(
            self.prenotazioni_context_state.get_free_slots(today)["Gate A"][1].start(),
            "11:00",
        )
        self.assertEqual(
            self.prenotazioni_context_state.get_free_slots(today)["Gate A"][1].stop(),
            "13:00",
        )

    def test_get_free_slots_handle_pauses_correctly(self):
        booker = IBooker(self.folder_prenotazioni)

        today = date.today()
        # need this just to have the day container
        aq_parent(
            booker.book(
                {
                    "booking_date": datetime(
                        today.year, today.month, today.day, 10, 30
                    ),
                    "booking_type": "Type A",
                    "title": "foo",
                }
            )
        )
        for hour in [7, 8, 9, 11, 12]:
            aq_parent(
                booker.book(
                    {
                        "booking_date": datetime(
                            today.year, today.month, today.day, hour, 00
                        ),
                        "booking_type": "Type A",
                        "title": "foo",
                    }
                )
            )

            aq_parent(
                booker.book(
                    {
                        "booking_date": datetime(
                            today.year, today.month, today.day, hour, 30
                        ),
                        "booking_type": "Type A",
                        "title": "foo",
                    }
                )
            )

        self.folder_prenotazioni.pause_table = [
            {"day": "0", "pause_end": "1030", "pause_start": "1000"},
            {"day": "1", "pause_end": "1030", "pause_start": "1000"},
            {"day": "2", "pause_end": "1030", "pause_start": "1000"},
            {"day": "3", "pause_end": "1030", "pause_start": "1000"},
            {"day": "4", "pause_end": "1030", "pause_start": "1000"},
            {"day": "5", "pause_end": "1030", "pause_start": "1000"},
            {"day": "6", "pause_end": "1030", "pause_start": "1000"},
            {"day": "7", "pause_end": "1030", "pause_start": "1000"},
        ]

        res = self.prenotazioni_context_state.get_free_slots(today)
        # there are no free slots because are all taken by bookings or pause
        self.assertEqual(len(res["Gate A"]), 0)

    def test_if_futureDays_is_not_set_maximum_bookable_date_return_none(self):
        logout()

        self.assertIsNone(self.prenotazioni_context_state.maximum_bookable_date)

    def test_if_futureDays_is_0_maximum_bookable_date_return_none(self):
        self.folder_prenotazioni.futureDays = 0
        logout()
        self.assertIsNone(self.prenotazioni_context_state.maximum_bookable_date)

    def test_if_futureDays_is_set_maximum_bookable_date_return_right_date_for_normal_users(
        self,
    ):
        self.folder_prenotazioni.futureDays = 2
        logout()
        self.assertEqual(
            self.prenotazioni_context_state.maximum_bookable_date.date(),
            self.today + timedelta(days=2),
        )

    def test_managers_bypass_futureDays_in_maximum_bookable_date(
        self,
    ):
        self.folder_prenotazioni.futureDays = 2
        self.assertIsNone(self.prenotazioni_context_state.maximum_bookable_date)

        logout()
        login(self.portal, "jdoe")
        self.assertIsNone(self.prenotazioni_context_state.maximum_bookable_date)

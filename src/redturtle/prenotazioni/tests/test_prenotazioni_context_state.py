# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime

from Acquisition import aq_parent
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

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

        self.api_session_admin = RelativeSession(self.portal_url)
        self.api_session_admin.headers.update({"Accept": "application/json"})
        self.api_session_admin.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
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

    def test_get_free_slots_skip_bookigs_inside_pause_range(self):
        booker = IBooker(self.folder_prenotazioni)

        today = date.today()
        # need this just to have the day container
        aq_parent(
            booker.create(
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

        view = api.content.get_view(
            context=self.folder_prenotazioni,
            request=self.request,
            name="prenotazioni_context_state",
        )
        res = view.get_free_slots(today)
        # available slots are only arount the pause and not inside it
        self.assertEqual(len(res["Gate A"]), 2)
        self.assertEqual(view.get_free_slots(today)["Gate A"][0].start(), "07:00")
        self.assertEqual(view.get_free_slots(today)["Gate A"][0].stop(), "08:00")
        self.assertEqual(view.get_free_slots(today)["Gate A"][1].start(), "11:00")
        self.assertEqual(view.get_free_slots(today)["Gate A"][1].stop(), "13:00")

    def test_get_free_slots_handle_pauses_correctly(self):
        booker = IBooker(self.folder_prenotazioni)

        today = date.today()
        # need this just to have the day container
        aq_parent(
            booker.create(
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
                booker.create(
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
                booker.create(
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

        view = api.content.get_view(
            context=self.folder_prenotazioni,
            request=self.request,
            name="prenotazioni_context_state",
        )
        res = view.get_free_slots(today)
        # there are no free slots because are all taken by bookings or pause
        self.assertEqual(len(res["Gate A"]), 0)

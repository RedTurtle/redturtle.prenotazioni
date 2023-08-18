# -*- coding: utf-8 -*-
from datetime import date
import transaction

from plone.app.testing import (
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    setRoles,
)
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING,
)
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING,
)
from plone import api

import unittest
import json


class TestContextState(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
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
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=[
                {
                    "day": "Lunedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [
                            {"day": "0", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "1", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "2", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "3", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "4", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "5", "pause_end": "1200", "pause_start": "1000"},
                        ],
                        "to_day": "18",
                        "week_table": [
                            {
                                "day": "Lunedì",
                                "morning_start": "1100",
                                "morning_end": "1200",
                                "afternoon_start": None,
                                "afternoon_end": None,
                            },
                        ],
                    }
                ]
            ),
        )
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

        self.view = api.content.get_view(
            name="prenotazioni_context_state",
            context=self.folder_prenotazioni,
            request=self.request,
        )

    def test_day_in_override_pause_table(self):
        now = date.today()
        res = self.view.get_pauses_in_day_folder(date(now.year, 1, 10))
        pause = res[0]
        self.assertEqual(pause.start, "10:00") and self.assertEqual(pause.stop, "12:00")

    def test_day_not_in_override_pause_table(self):
        now = date.today()
        res = self.view.get_pauses_in_day_folder(date(now.year, 6, 10))
        pause = res[0]
        self.assertNotEqual(pause.start, "10:00") and self.assertNotEqual(
            pause.stop, "12:00"
        )


class TestAPIPost(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
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
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=[
                {
                    "day": "Lunedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [
                            {"day": "0", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "1", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "2", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "3", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "4", "pause_end": "1200", "pause_start": "1000"},
                            {"day": "5", "pause_end": "1200", "pause_start": "1000"},
                        ],
                        "to_day": "18",
                        "week_table": [
                            {
                                "day": "Lunedì",
                                "morning_start": "1100",
                                "morning_end": "1200",
                                "afternoon_start": None,
                                "afternoon_end": None,
                            },
                        ],
                    }
                ]
            ),
        )
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        self.view = api.content.get_view(
            name="prenotazioni_context_state",
            context=self.folder_prenotazioni,
            request=self.request,
        )

    def tearDown(self):
        self.api_session.close()

    def test_add_booking_in_overrided_pause(self):
        self.api_session.auth = None
        booking_date = "{}T11:00:00+00:00".format(
            (date(date.today().year, 1, 10)).strftime("%Y-%m-%d")
        )

        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": "Type A",
                "fields": [
                    {"name": "fullname", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertNotEqual(res.status_code, 200)

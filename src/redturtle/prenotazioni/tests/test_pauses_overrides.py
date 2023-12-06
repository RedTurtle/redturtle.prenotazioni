# -*- coding: utf-8 -*-
import json
import unittest
from datetime import date

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


class TestPausesOverride(unittest.TestCase):
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
            daData=date.today(),
            gates=["Gate A"],
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [
                            {
                                "day": "0",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "1",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "2",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "3",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "4",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "5",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                        ],
                        "to_day": "18",
                        "week_table": [],
                    }
                ]
            ),
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
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
        self.assertEqual(pause.start, "09:00") and self.assertNotEqual(
            pause.stop, "09:15"
        )

    def test_if_pause_override_not_set_use_default(self):
        folder = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            daData=date.today(),
            gates=["Gate A"],
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [],
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

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder,
            gates=["all"],
        )

        view = api.content.get_view(
            name="prenotazioni_context_state",
            context=folder,
            request=self.request,
        )
        now = date.today()
        res = view.get_pauses_in_day_folder(date(now.year, 1, 10))
        pause = res[0]
        self.assertEqual(pause.start, "09:00") and self.assertNotEqual(
            pause.stop, "09:15"
        )


class TestPauseOverrideAPIPost(unittest.TestCase):
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
            daData=date.today(),
            gates=["Gate A"],
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [
                            {
                                "day": "0",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "1",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "2",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "3",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "4",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                            {
                                "day": "5",
                                "pause_end": "1200",
                                "pause_start": "1000",
                            },
                        ],
                        "to_day": "18",
                        "week_table": [],
                    }
                ]
            ),
        )

        booking_type_A = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        api.content.transition(obj=booking_type_A, transition="publish")
        self.folder_prenotazioni.reindexObject(idxs=["review_state"])
        booking_type_A.reindexObject(idxs=["review_state"])

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

    def test_add_booking_in_overrided_pause_return_400(self):
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
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()["message"], "Sorry, this slot is not available anymore."
        )

    def test_add_booking_outside_overrided_pause_return_200(self):
        self.api_session.auth = None
        booking_date = "{}T09:00:00+00:00".format(
            (date(date.today().year, 1, 10)).strftime("%Y-%m-%d")
        )

        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 200)

    def test_if_pause_override_not_set_use_default(self):
        folder = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            daData=date.today(),
            gates=["Gate A"],
            pause_table=[
                {"day": "0", "pause_start": "0900", "pause_end": "0915"},
                {"day": "1", "pause_start": "0900", "pause_end": "0915"},
                {"day": "2", "pause_start": "0900", "pause_end": "0915"},
                {"day": "3", "pause_start": "0900", "pause_end": "0915"},
                {"day": "4", "pause_start": "0900", "pause_end": "0915"},
                {"day": "5", "pause_start": "0900", "pause_end": "0915"},
            ],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [],
                        "to_day": "18",
                        "week_table": [],
                    }
                ]
            ),
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder,
            gates=["all"],
        )

        transaction.commit()

        booking_date = "{}T09:00:00+00:00".format(
            (date(date.today().year, 1, 10)).strftime("%Y-%m-%d")
        )

        res = self.api_session.post(
            folder.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 400)

        res = self.api_session.post(
            folder.absolute_url() + "/@booking",
            json={
                "booking_date": "{}T10:00:00+00:00".format(
                    (date(date.today().year, 1, 10)).strftime("%Y-%m-%d")
                ),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 200)

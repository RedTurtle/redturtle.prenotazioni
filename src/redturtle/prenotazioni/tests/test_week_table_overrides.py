# -*- coding: utf-8 -*-
import json
import unittest
from datetime import date

from freezegun import freeze_time
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


class TestWeekTableOverridesContextState(unittest.TestCase):
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
                        "to_day": "1",
                        "to_month": "2",
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
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        self.view = api.content.get_view(
            name="prenotazioni_context_state",
            context=self.folder_prenotazioni,
            request=self.request,
        )

    def test_if_day_not_in_overrides_use_default_week_table(self):
        now = date.today()
        res = self.view.get_week_table(date(now.year, 6, 1))

        self.assertEqual(res, self.folder_prenotazioni.week_table)

    def test_if_day_is_in_overrides_use_override_week_table(self):
        now = date.today()
        res = self.view.get_week_table(date(now.year, 1, 10))
        self.assertEqual(
            res,
            json.loads(self.folder_prenotazioni.week_table_overrides)[0]["week_table"],
        )

    @freeze_time("2023-05-14")
    def test_override_between_year(self):
        self.folder_prenotazioni.week_table_overrides = json.dumps(
            [
                {
                    "from_day": "1",
                    "from_month": "12",
                    "to_day": "1",
                    "to_month": "3",
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
        )
        now = date.today()

        # if in range, return table overrides
        self.assertEqual(
            self.view.get_week_table(date(now.year, 12, 25)),
            json.loads(self.folder_prenotazioni.week_table_overrides)[0]["week_table"],
        )

        # if in range and next year, return table overrides
        self.assertEqual(
            self.view.get_week_table(date(now.year + 1, 1, 25)),
            json.loads(self.folder_prenotazioni.week_table_overrides)[0]["week_table"],
        )

        # if in range and next year +1, return table overrides
        self.assertEqual(
            self.view.get_week_table(date(now.year + 1, 12, 25)),
            json.loads(self.folder_prenotazioni.week_table_overrides)[0]["week_table"],
        )

        # if out of range, return base table
        self.assertEqual(
            self.view.get_week_table(date(now.year, 10, 10)),
            self.folder_prenotazioni.week_table,
        )


class TestWeekTableOverridesApiValidateDataOnPost(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        self.api_session.close()

    def test_correct_settings(self):
        data = [
            {
                "from_day": "1",
                "from_month": "1",
                "to_day": "1",
                "to_month": "2",
                "week_table": [
                    {
                        "day": "Lunedì",
                        "morning_start": "0700",
                        "morning_end": "1000",
                        "afternoon_start": None,
                        "afternoon_end": None,
                    },
                ],
            }
        ]

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_date_range_required(self):
        data = [
            {
                "from_day": "",
                "from_month": "",
                "to_day": "",
                "to_month": "",
                "week_table": [
                    {
                        "day": "Lunedì",
                        "morning_start": "0700",
                        "morning_end": "1000",
                        "afternoon_start": None,
                        "afternoon_end": None,
                    },
                ],
            }
        ]

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set a start range.",
            response.json()["message"],
        )

        data[0]["from_day"] = "1"
        data[0]["from_month"] = "1"

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set an end range.",
            response.json()["message"],
        )

    def test_wrong_day_based_on_month(self):
        data = [
            {
                "from_day": "40",
                "from_month": "1",
                "to_day": "1",
                "to_month": "2",
                "week_table": [
                    {
                        "day": "Lunedì",
                        "morning_start": "0700",
                        "morning_end": "1000",
                        "afternoon_start": None,
                        "afternoon_end": None,
                    },
                ],
            }
        ]

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Selected day is too big for that month for "from" field.',
            response.json()["message"],
        )

        data[0]["from_day"] = "1"
        data[0]["to_day"] = "32"

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Selected day is too big for that month for "to" field.',
            response.json()["message"],
        )

    def test_if_set_start_you_should_set_an_end(self):
        data = [
            {
                "from_day": "1",
                "from_month": "1",
                "to_day": "1",
                "to_month": "2",
                "week_table": [
                    {
                        "day": "Lunedì",
                        "morning_start": "0700",
                        "morning_end": "",
                        "afternoon_start": "",
                        "afternoon_end": "",
                    },
                ],
            }
        ]

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set an end time for morning",
            response.json()["message"],
        )

    def test_if_set_end_you_should_set_a_start(self):
        data = [
            {
                "from_day": "1",
                "from_month": "1",
                "to_day": "1",
                "to_month": "2",
                "week_table": [
                    {
                        "day": "Lunedì",
                        "morning_start": "",
                        "morning_end": "1000",
                        "afternoon_start": "",
                        "afternoon_end": "",
                    },
                ],
            }
        ]

        response = self.api_session.post(
            self.portal_url,
            json={
                "@type": "PrenotazioniFolder",
                "title": "Example",
                "daData": json_compatible(date.today()),
                "week_table_overrides": json.dumps(data),
                "same_day_booking_disallowed": "yes",
                "gates": ["Gate A"],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set a start time for morning",
            response.json()["message"],
        )

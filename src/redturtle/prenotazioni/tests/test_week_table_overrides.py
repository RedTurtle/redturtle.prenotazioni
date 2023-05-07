# -*- coding: utf-8 -*-
from plone.restapi.serializer.converters import json_compatible
from datetime import date
from plone.app.testing import (
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    setRoles,
)
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

import unittest
import json


class TestOverridesValidator(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set an end time for morning", response.json()["message"]
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
                "booking_types": [
                    {"name": "Type A", "duration": "30"},
                ],
                "gates": ["Gate A"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You should set a start time for morning", response.json()["message"]
        )

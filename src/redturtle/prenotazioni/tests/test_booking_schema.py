# -*- coding: utf-8 -*-
from datetime import date
from plone import api
from plone.app.testing import (
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    setRoles,
)
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from plone.restapi.serializer.converters import json_compatible

import unittest
import transaction


class TestMonthSlots(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

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
                {
                    "day": "Martedì",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Mercoledì",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Giovedì",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Venerdì",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Sabato",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Domenica",
                    "morning_start": None,
                    "morning_end": None,
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
            required_booking_fields=["email", "fiscalcode"],
        )

        year = api.content.create(
            container=self.folder_prenotazioni, type="PrenotazioniYear", title="Year"
        )
        week = api.content.create(container=year, type="PrenotazioniWeek", title="Week")
        self.day_folder = api.content.create(
            container=week, type="PrenotazioniDay", title="Day"
        )
        transaction.commit()

    def test_booking_schema_called_without_params_return_error(
        self,
    ):

        response = self.api_session.get(
            "{}/@prenotazione-schema".format(self.folder_prenotazioni.absolute_url())
        )
        expected = "Wrong date format"

        self.assertIn(expected, response.text)

    def test_booking_schema_no_bookable_available(
        self,
    ):
        now = date.today()
        current_year = now.year
        sunday = 6
        current_month = now.month

        response = self.api_session.get(
            "{}/@prenotazione-schema?form.booking_date={}+10%3A00".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(current_year, current_month, sunday)),
            ),
        )

        expected = {
            "booking_types": {
                "bookable": [],
                "unbookable": [{"duration": "30", "name": "Type A"}],
            },
            "fields": [
                {"name": "email", "readonly": True, "required": True, "value": ""},
                {"name": "phone", "readonly": True, "required": False, "value": ""},
                {
                    "name": "description",
                    "readonly": True,
                    "required": False,
                    "value": "",
                },
                {"name": "title", "readonly": True, "required": True, "value": ""},
            ],
        }

        self.assertEqual(expected, response.json())

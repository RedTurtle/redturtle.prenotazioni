# -*- coding: utf-8 -*-
import calendar
import unittest
from datetime import date

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestBookingSchema(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
    maxDiff = None

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
            gates=["Gate A"],
            required_booking_fields=["email", "fiscalcode"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        year = api.content.create(
            container=self.folder_prenotazioni,
            type="PrenotazioniYear",
            title="Year",
        )
        week = api.content.create(container=year, type="PrenotazioniWeek", title="Week")
        self.day_folder = api.content.create(
            container=week, type="PrenotazioniDay", title="Day"
        )
        transaction.commit()

    def tearDown(self):
        self.api_session.close()

    def test_booking_schema_called_without_params_return_error(
        self,
    ):
        response = self.api_session.get(
            "{}/@booking-schema".format(self.folder_prenotazioni.absolute_url())
        )

        expected = (
            "You need to provide a booking date to get the schema and available types."
        )

        self.assertIn(expected, response.json().get("message"))

    def test_booking_schema_no_bookable_available(
        self,
    ):
        now = date.today()
        current_year = now.year
        sunday = 6
        current_month = now.month

        response = self.api_session.get(
            "{}/@booking-schema?booking_date={}+10%3A00".format(
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
                {
                    "desc": "Inserire il nome completo",
                    "label": "Nome completo",
                    "name": "title",
                    "readonly": False,
                    "required": True,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Inserisci l'email",
                    "label": "Email",
                    "name": "email",
                    "readonly": False,
                    "required": True,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Inserisci il numero di telefono",
                    "label": "Numero di telefono",
                    "name": "phone",
                    "readonly": False,
                    "required": False,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Aggiungi ulteriori dettagli",
                    "label": "Note",
                    "name": "description",
                    "readonly": False,
                    "required": False,
                    "type": "textarea",
                    "value": "",
                },
            ],
        }
        self.assertEqual(expected, response.json())

    def test_booking_schema_bookable_available(
        self,
    ):
        now = date.today()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        monday = 0
        # get next monday
        found = False
        while not found:
            for week in calendar.monthcalendar(current_year, current_month):
                # week[0] is monday and should be greater than today
                if week[0] > current_day:
                    monday = week[0]
                    found = True
                    break

            if monday == 0:
                current_month += 1
                current_day = 1

        response = self.api_session.get(
            "{}/@booking-schema?booking_date={}+07%3A00".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(current_year, current_month, monday)),
            ),
        )

        expected = {
            "booking_types": {
                "bookable": [{"duration": "30", "name": "Type A"}],
                "unbookable": [],
            },
            "fields": [
                {
                    "desc": "Inserire il nome completo",
                    "label": "Nome completo",
                    "name": "title",
                    "readonly": False,
                    "required": True,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Inserisci l'email",
                    "label": "Email",
                    "name": "email",
                    "readonly": False,
                    "required": True,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Inserisci il numero di telefono",
                    "label": "Numero di telefono",
                    "name": "phone",
                    "readonly": False,
                    "required": False,
                    "type": "text",
                    "value": "",
                },
                {
                    "desc": "Aggiungi ulteriori dettagli",
                    "label": "Note",
                    "name": "description",
                    "readonly": False,
                    "required": False,
                    "type": "textarea",
                    "value": "",
                },
            ],
        }

        self.assertEqual(expected, response.json())

# -*- coding: utf-8 -*-
import calendar
import unittest
from datetime import date
from datetime import datetime

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestBookingInfo(unittest.TestCase):
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
            gates=["Gate A"],
            required_booking_fields=["email", "fiscalcode"],
            visible_booking_field=["email", "fiscalcode"],
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

    def test_create_booking_and_check_details(
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
        # create a placeholder for first available monday

        booker = IBooker(self.folder_prenotazioni)
        booking = booker.create(
            {
                "booking_date": datetime(current_year, current_month, monday, 7, 0),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()

        booking_uid = booking.UID()

        response = self.api_session.get(
            "{}/@booking/{}".format(
                self.folder_prenotazioni.absolute_url(), booking_uid
            )
        )

        self.assertIn("email", response.json())
        self.assertIn("fiscalcode", response.json())

    def test_get_booking_without_UID(
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
        # create a placeholder for first available monday

        booker = IBooker(self.folder_prenotazioni)
        booker.create(
            {
                "booking_date": datetime(current_year, current_month, monday, 7, 0),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()

        response = self.api_session.get(
            "{}/@booking".format(self.folder_prenotazioni.absolute_url())
        )

        self.assertEqual(404, response.status_code)

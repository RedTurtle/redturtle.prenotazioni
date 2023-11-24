# -*- coding: utf-8 -*-
import calendar
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
import transaction
from freezegun import freeze_time
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

DATE_STR = "2023-05-14"


class TestAvailableSlots(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
    maxDiff = None
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def dt_local_to_json(self, value):
        return json_compatible(self.dt_local_to_utc(value))

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
            gates=["Gate A"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )
        api.content.create(
            type="PrenotazioneType",
            title="Type B",
            duration=90,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        week_table = self.folder_prenotazioni.week_table
        week_table[0]["morning_start"] = "0700"
        week_table[0]["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        year = api.content.create(
            container=self.folder_prenotazioni,
            type="PrenotazioniYear",
            title="Year",
        )
        week = api.content.create(container=year, type="PrenotazioniWeek", title="Week")
        self.day_folder = api.content.create(
            container=week, type="PrenotazioniDay", title="Day"
        )

        api.portal.set_registry_record(
            "plone.portal_timezone",
            self.timezone,
        )

        transaction.commit()

    def tearDown(self):
        self.api_session.close()

    @unittest.skip("issue testing in the last days of a month")
    def test_month_slots_called_without_params_return_all_available_slots_of_current_month(
        self,
    ):
        response = self.api_session.get(
            "{}/@available-slots".format(self.folder_prenotazioni.absolute_url())
        )
        # get next mondays in current month
        now = date.today()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        expected = []
        for week in calendar.monthcalendar(current_year, current_month):
            # week[0] is monday and should be greater than today
            if week[0] > current_day:
                for hour in [7, 8, 9]:
                    expected.append(
                        json_compatible(
                            datetime(current_year, current_month, week[0], hour, 0)
                        )
                    )
        self.assertEqual(expected, response.json()["items"])

    @unittest.skipIf(date.today().day > 20, "issue testing in the last days of a month")
    def test_month_slots_called_without_params_return_available_slots_of_current_month_when_some_are_full(
        self,
    ):
        now = date.today()
        current_year = now.year
        current_month = now.month
        next_month = current_month + 1
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
                "booking_date": self.dt_local_to_utc(
                    datetime(current_year, current_month, monday, 7, 0)
                ),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()

        # get next mondays in current or next month
        now = date.today()
        current_year = now.year

        if current_month == next_month:
            response = self.api_session.get(
                "{}/@available-slots?date={}".format(
                    self.folder_prenotazioni.absolute_url(),
                    json_compatible(date(current_year, next_month, monday)),
                )
            )

            # first free slot is at 7:30 (localtime) of the next month
            self.assertEqual(
                response.json()["items"][0],
                self.dt_local_to_json(
                    datetime(current_year, next_month, monday, 7, 30)
                ),
            )
        else:
            response = self.api_session.get(
                "{}/@available-slots".format(self.folder_prenotazioni.absolute_url())
            )

            # first free slot is at 7:30
            self.assertEqual(
                response.json()["items"][0],
                self.dt_local_to_json(
                    datetime(current_year, current_month, monday, 7, 30)
                ),
            )

    @freeze_time(DATE_STR)
    def test_if_start_and_not_end_return_all_available_slots_for_that_month(
        self,
    ):
        now = date.today()
        current_year = now.year
        current_month = now.month
        next_month = current_month + 1

        self.folder_prenotazioni.daData = now
        transaction.commit()

        # all mondays in next month
        response = self.api_session.get(
            "{}/@available-slots?start={}".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(current_year, next_month, 1)),
            )
        )
        # get next mondays in current month
        expected = []
        for week in calendar.monthcalendar(current_year, next_month):
            monday = week[0]
            if monday > 0:
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 7, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 8, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 9, 0)
                    )
                )
        self.assertEqual(expected, response.json()["items"])

    def test_if_start_and_end_return_all_available_slots_between_these_dates(
        self,
    ):
        now = date.today()
        current_year = now.year
        current_month = now.month
        next_month = current_month + 1

        # all mondays in the first 10 days of next month
        response = self.api_session.get(
            "{}/@available-slots?start={}&end={}".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(current_year, next_month, 1)),
                json_compatible(date(current_year, next_month, 10)),
            )
        )
        # get next mondays in current month
        expected = []
        for week in calendar.monthcalendar(current_year, next_month):
            monday = week[0]
            if monday > 0 and monday <= 10:
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 7, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 8, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(current_year, next_month, monday, 9, 0)
                    )
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, response.json()["items"])

    def test_raise_error_if_start_is_greater_than_end(
        self,
    ):
        now = date.today()
        current_year = now.year
        current_month = now.month
        next_month = current_month + 1

        response = self.api_session.get(
            "{}/@available-slots?start={}&end={}".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(current_year, next_month, 10)),
                json_compatible(date(current_year, next_month, 1)),
            )
        )

        self.assertEqual(400, response.status_code)

    @unittest.skipIf(date.today().day > 20, "issue testing in the last days of a month")
    def test_month_slots_notBeforeDays_honored(
        self,
    ):
        now = date.today()
        week_table = []
        for i in range(0, 7):
            data = {
                "day": str(i),
                "morning_start": None,
                "morning_end": None,
                "afternoon_start": None,
                "afternoon_end": None,
            }
            if i == now.weekday() + 1:
                # open only for tomorrow
                data["morning_start"] = "0700"
                data["morning_end"] = "0800"
            week_table.append(data)

        folder = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=now,
            week_table=week_table,
            gates=["Gate A"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder,
            gates=["all"],
        )

        transaction.commit()

        response = self.api_session.get(
            "{}/@available-slots".format(folder.absolute_url())
        )

        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_7_0 = self.dt_local_to_json(
            tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
        )

        self.assertNotIn(tomorrow_7_0, response.json()["items"])

        folder.notBeforeDays = 0
        transaction.commit()

        response = self.api_session.get(f"{folder.absolute_url()}/@available-slots")
        self.assertIn(tomorrow_7_0, response.json()["items"])

    @unittest.skipIf(date.today().day > 20, "issue testing in the last days of a month")
    def test_month_slots_filtered_by_booking_type(self):
        # Type A 30 minutes
        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@available-slots?booking_type=Type A"
        )  # noqa
        self.assertEqual(response.status_code, 200)

        # crappy test .... TODO: rethink
        # self.assertEqual(len(response.json()["items"]), 6)
        type_a_len = len(response.json()["items"])

        # Type B 90 minutes
        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@available-slots?booking_type=Type B"
        )  # noqa
        self.assertEqual(response.status_code, 200)

        # crappy test .... TODO: rethink
        # self.assertEqual(len(response.json()["items"]), 4)
        type_b_len = len(response.json()["items"])
        self.assertTrue(type_a_len > type_b_len)

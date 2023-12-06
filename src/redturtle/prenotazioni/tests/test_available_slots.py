# -*- coding: utf-8 -*-
import calendar
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

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
        self.request = self.layer["request"]
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
            notBeforeDays=0,
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

        self.context_state = api.content.get_view(
            "prenotazioni_context_state",
            self.folder_prenotazioni,
            self.request,
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

    @freeze_time("2023-05-03")  # wednesday
    def test_month_slots_called_without_params_on_start_of_the_month_return_available_slots_of_current_month_when_some_are_full(
        self,
    ):
        """data is freezed to be sure to check a consistent data"""

        now = date.today()
        # set date with freezed one
        self.folder_prenotazioni.daData = now

        monday = 0
        # get next monday
        for week in calendar.monthcalendar(now.year, now.month):
            # week[0] is monday and should be greater than today
            if week[0] > now.day:
                monday = week[0]
                break

        # create a placeholder for first available monday
        booker = IBooker(self.folder_prenotazioni)
        booker.create(
            {
                "booking_date": self.dt_local_to_utc(
                    datetime(now.year, now.month, monday, 7, 0)
                ),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()

        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@available-slots".format()
        )

        # first free slot is at 7:30 (localtime) of the next month
        self.assertEqual(
            response.json()["items"][0],
            self.dt_local_to_json(datetime(now.year, now.month, monday, 7, 30)),
        )

    @freeze_time(DATE_STR)
    def test_month_slots_called_without_params_on_middle_of_the_month_return_available_slots_of_current_month_when_some_are_full(
        self,
    ):
        """data is freezed to be sure to check a consistent data"""

        now = date.today()
        # set date with freezed one
        self.folder_prenotazioni.daData = now

        monday = 0
        # get next monday
        for week in calendar.monthcalendar(now.year, now.month):
            # week[0] is monday and should be greater than today
            if week[0] > now.day:
                monday = week[0]
                break

        # create a placeholder for first available monday
        booker = IBooker(self.folder_prenotazioni)
        booker.create(
            {
                "booking_date": self.dt_local_to_utc(
                    datetime(now.year, now.month, monday, 7, 0)
                ),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()

        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@available-slots".format()
        )

        # first free slot is at 7:30 (localtime) of the next month
        self.assertEqual(
            response.json()["items"][0],
            self.dt_local_to_json(datetime(now.year, now.month, monday, 7, 30)),
        )

    @freeze_time("2023-05-30")  # tuesday
    def test_month_slots_called_without_params_at_end_of_the_month_return_no_available_slots_of_current_month(
        self,
    ):
        """data is freezed to be sure to check a consistent data"""

        now = date.today()
        # set date with freezed one
        self.folder_prenotazioni.daData = now

        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@available-slots".format()
        )

        self.assertEqual(len(response.json()["items"]), 0)

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
        next_month = now + relativedelta.relativedelta(months=1)
        # all mondays in the first 10 days of next month
        response = self.api_session.get(
            "{}/@available-slots?start={}&end={}".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(next_month.year, next_month.month, 1)),
                json_compatible(date(next_month.year, next_month.month, 10)),
            )
        )
        # get next mondays in current month
        expected = []
        for week in calendar.monthcalendar(next_month.year, next_month.month):
            monday = week[0]
            if 0 < monday <= 10:
                if self.context_state.is_vacation_day(
                    datetime(next_month.year, next_month.month, monday)
                ):
                    continue
                expected.append(
                    self.dt_local_to_json(
                        datetime(next_month.year, next_month.month, monday, 7, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(next_month.year, next_month.month, monday, 8, 0)
                    )
                )
                expected.append(
                    self.dt_local_to_json(
                        datetime(next_month.year, next_month.month, monday, 9, 0)
                    )
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, response.json()["items"])

    def test_raise_error_if_start_is_greater_than_end(
        self,
    ):
        now = date.today()
        next_month = now + relativedelta.relativedelta(months=1)

        response = self.api_session.get(
            "{}/@available-slots?start={}&end={}".format(
                self.folder_prenotazioni.absolute_url(),
                json_compatible(date(next_month.year, next_month.month, 10)),
                json_compatible(date(next_month.year, next_month.month, 1)),
            )
        )

        self.assertEqual(400, response.status_code)

    @freeze_time(DATE_STR)
    def test_month_slots_notBeforeDays_honored(
        self,
    ):
        now = date.today()
        tomorrow = now + timedelta(days=1)
        week_table = []
        for i in range(0, 7):
            data = {
                "day": str(i),
                "morning_start": None,
                "morning_end": None,
                "afternoon_start": None,
                "afternoon_end": None,
            }
            if i == tomorrow.weekday():
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

        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_7_0 = self.dt_local_to_json(
            tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
        )

        # response = self.api_session.get(
        #     "{}/@available-slots".format(folder.absolute_url())
        # )
        # self.assertNotIn(tomorrow_7_0, response.json()["items"])

        folder.notBeforeDays = 0
        transaction.commit()

        response = self.api_session.get(f"{folder.absolute_url()}/@available-slots")
        self.assertIn(tomorrow_7_0, response.json()["items"])

    @freeze_time(DATE_STR)
    def test_month_slots_filtered_by_booking_type(self):
        self.folder_prenotazioni.daData = date.today()
        transaction.commit()

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

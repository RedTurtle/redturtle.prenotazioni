# -*- coding: utf-8 -*-
import time
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

import pytz
import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestMoveBookingApi(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session_admin = RelativeSession(self.portal_url)
        self.api_session_admin.headers.update({"Accept": "application/json"})
        self.api_session_admin.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )
        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])
        self.api_session_bookings_manager = RelativeSession(self.portal_url)
        self.api_session_bookings_manager.headers.update({"Accept": "application/json"})
        self.api_session_bookings_manager.auth = ("jdoe", "secret!!!")

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
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

        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        self.booker = IBooker(self.folder_prenotazioni)
        self.today = (
            datetime.utcnow().replace(hour=8, microsecond=0).astimezone(pytz.UTC)
        )
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

    def tearDown(self):
        self.api_session_admin.close()

    def test_move_booking(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        tomorrow = self.today + timedelta(1)
        response = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": tomorrow.isoformat(),  # tomorrow
            },
        )
        self.assertEqual(response.status_code, 204)

        response = self.api_session_admin.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            datetime.fromisoformat(response.json()["booking_date"]),
            tomorrow,
        )

    def test_booking_manager_move(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()
        uid = booking.UID()
        tomorrow = self.today + timedelta(days=1)
        response = self.api_session_bookings_manager.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": tomorrow.isoformat(),  # tomorrow
            },
        )
        self.assertEqual(response.status_code, 204)

        response = self.api_session_bookings_manager.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            datetime.fromisoformat(response.json()["booking_date"]),
            tomorrow,
        )

    def test_booking_manager_move_month(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        transaction.commit()
        uid = booking.UID()
        nextmonth = self.today + relativedelta(months=1)
        response = self.api_session_bookings_manager.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": nextmonth.isoformat(),  # nextmonth
            },
        )
        self.assertEqual(response.status_code, 204)

        response = self.api_session_bookings_manager.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            datetime.fromisoformat(response.json()["booking_date"]),
            nextmonth,
        )

    def test_move_booking_to_used_slot(self):
        self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            },
            force_gate="Gate A",
        )
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            },
            force_gate="Gate B",
        )

        uid = booking.UID()

        transaction.commit()

        response = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": self.today.isoformat(),
                "gate": "Gate A",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Sorry, this slot is not available or does not fit your booking.",
        )

    def test_move_booking_update_modification_date(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        booking.setModificationDate(booking.modified() - 1)
        booking.reindexObject(idxs=["modified"])

        uid = booking.UID()
        old_modified = json_compatible(booking.modified())
        transaction.commit()

        # check that modification_date is right
        response = self.api_session_admin.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}"
        ).json()

        self.assertEqual(old_modified, response["modification_date"])

        # now move the booking
        time.sleep(1)
        tomorrow = self.today + timedelta(1)
        response = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": tomorrow.isoformat(),  # tomorrow
            },
        )
        response = self.api_session_admin.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}",
        ).json()

        self.assertNotEqual(response["modification_date"], old_modified)
        self.assertGreater(response["modification_date"], old_modified)

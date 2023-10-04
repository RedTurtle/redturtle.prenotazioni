# -*- coding: UTF-8 -*-
import unittest
from datetime import date, datetime, timedelta

from plone import api
from plone.app.testing import (
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    setRoles,
)
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.testing import RelativeSession
from transaction import commit
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestDaySlots(unittest.TestCase):
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
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
            max_bookings_allowed=100,
        )
        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        self.today = datetime.now().replace(hour=8)
        self.tomorrow = self.today + timedelta(1)

        api.portal.set_registry_record(
            "plone.portal_timezone",
            "Europe/Rome",
        )

        commit()

    def create_booking(self, date):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(
            {
                "booking_date": date,  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            },
        )

    def test_bookings_returned_by_gate(self):
        bookings = [
            self.create_booking(self.tomorrow + timedelta(minutes=i * 30))
            for i in range(5)
        ]
        commit()

        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day/{self.tomorrow.isoformat()}"
        )
        self.assertEqual(response.status_code, 200)

        results = response.json()["bookings"]["Gate A"]

        for booking in bookings:
            self.assertIn(
                getMultiAdapter((booking, getRequest()), ISerializeToJson)(),
                results,
            )

    def test_pauses_returned(self):
        # le pause sono in localtime
        self.folder_prenotazioni.pause_table = [
            {
                "day": str(self.tomorrow.weekday()),
                "pause_start": "0715",
                "pause_end": "0830",
            }
        ]
        commit()
        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day/{self.tomorrow.isoformat()}"
        )
        self.assertEqual(response.status_code, 200)

        results = response.json()["pauses"]
        # la risposta è in UTC
        self.assertIn(
            {
                "start": self.tomorrow.strftime("%Y-%m-%d") + "T05:15:00+00:00",
                "end": self.tomorrow.strftime("%Y-%m-%d") + "T06:30:00+00:00",
            },
            results,
        )

    def test_bad_request_date(self):
        res = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day/fff"
        )
        self.assertEqual(res.json()["type"], "BadRequest")
        self.assertEqual(res.status_code, 400)

    def test_daily_schedule(self):
        # TODO: testare con timezone differenti
        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day/{self.tomorrow.isoformat()}"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()

        self.assertIn("daily_schedule", results)
        # sul database gli orari sono in localtime
        self.assertEqual(
            self.folder_prenotazioni.week_table[0]["morning_start"], "0700"
        )
        self.assertEqual(self.folder_prenotazioni.week_table[0]["morning_end"], "1000")
        # la risposta è in UTC
        self.assertEqual(
            {
                "afternoon": {"start": None, "end": None},
                "morning": {
                    "start": self.tomorrow.strftime("%Y-%m-%d") + "T05:00:00+00:00",
                    "end": self.tomorrow.strftime("%Y-%m-%d") + "T08:00:00+00:00",
                },
            },
            results["daily_schedule"],
        )

    def test_gates_returned(self):
        # TODO: testare con timezone differenti
        response = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day/{self.tomorrow.isoformat()}"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()

        self.assertIn("gates", results)
        self.assertEqual(
            [{"name": "Gate A", "available": True}],
            results["gates"],
        )

    # TODO: test vacation slots

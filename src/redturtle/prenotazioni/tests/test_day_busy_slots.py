# -*- coding: UTF-8 -*-
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING,
)

from datetime import date, datetime
from datetime import timedelta
from transaction import commit

import unittest


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestSendIcal(unittest.TestCase):
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
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Mercoledì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Giovedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Venerdì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Sabato",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Domenica",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
        )
        self.today = datetime.now().replace(hour=8)
        self.tomorrow = self.today + timedelta(1)

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

        results = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day-busy-slots?date={self.tomorrow.strftime('%d/%m/%Y')}"
        ).json()["bookings"]["Gate A"]

        for booking in bookings:
            self.assertIn(
                getMultiAdapter((booking, getRequest()), ISerializeToJson)(),
                results,
            )

    def test_pauses_returned(self):
        self.folder_prenotazioni.pause_table = [
            {
                "day": str(self.tomorrow.weekday()),
                "pause_start": "0715",
                "pause_end": "0830",
            }
        ]

        commit()

        results = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day-busy-slots?date={self.tomorrow.strftime('%d/%m/%Y')}"
        ).json()["pauses"]

        self.assertIn(
            {
                "start": "07:15",
                "stop": "08:30",
            },
            results,
        )

    def test_bad_request_date(self):
        res = self.api_session.get(
            f"{self.folder_prenotazioni.absolute_url()}/@day-busy-slots?date=fff"
        )

        self.assertEquals(res.json()["type"], "BadRequest")
        self.assertEquals(res.status_code, 400)
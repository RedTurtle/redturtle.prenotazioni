# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestVacationgApi(unittest.TestCase):
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

        self.api_session_anon = RelativeSession(self.portal_url)
        self.api_session_anon.headers.update({"Accept": "application/json"})

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            same_day_booking_disallowed="no",
        )

        booking_type_A = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        api.content.transition(
            booking_type_A,
            transition="publish",
        )
        booking_type_A.reindexObject(idxs=["review_state"])

        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1200"
        self.folder_prenotazioni.week_table = week_table

        self.next_monday = datetime.now().replace(second=0, microsecond=0).astimezone(
            pytz.utc
        ) + timedelta(days=(datetime.today().weekday()) % 7 + 7)

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")

        api.portal.set_registry_record(
            "plone.portal_timezone",
            "Europe/Rome",
        )

        transaction.commit()

    def tearDown(self):
        self.api_session_admin.close()
        self.api_session_anon.close()

    @unittest.skipIf(
        date.today().day >= 20 or date.today().day <= 8,
        "issue testing in the last days of a month",
    )
    def test_add_vacation(self):
        # UTC time
        start = self.next_monday.replace(hour=8, minute=0)
        end = self.next_monday.replace(hour=9, minute=30)
        gate = self.folder_prenotazioni.gates[0]
        res = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@vacation",
            json={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "gate": gate,
                "title": "vacation foo",
            },
        )
        self.assertEqual(res.status_code, 204)

        res = self.api_session_anon.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": start.isoformat(),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 200)
        # gates[0] is busy because of vacation
        self.assertEqual(res.json()["gate"], self.folder_prenotazioni.gates[1])

        # both gates are busy (one for vacation, one for booking)
        res = self.api_session_anon.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": start.isoformat(),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()["message"],
            "Sorry, this slot is not available anymore.",
        )

    def test_add_vacation_wrong_hours(self):
        # add vacation outside of working hours
        # UTC time
        start = self.next_monday.replace(hour=20, minute=0)
        end = self.next_monday.replace(hour=21, minute=30)
        gate = self.folder_prenotazioni.gates[0]
        res = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@vacation",
            json={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "gate": gate,
                "title": "vacation foo",
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()["message"],
            "This day is not valid.",
        )

        # add vacation when there is already a booking
        res = self.api_session_anon.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": self.next_monday.replace(hour=10, minute=0).isoformat(),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

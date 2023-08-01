# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

import transaction
import unittest


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
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A", "Gate B"],
            same_day_booking_disallowed="no",
        )
        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1200"
        self.folder_prenotazioni.week_table = week_table

        self.next_monday = datetime.now() + timedelta(
            days=(datetime.today().weekday()) % 7 + 7
        )

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

    def tearDown(self):
        self.api_session_admin.close()
        self.api_session_anon.close()

    # TODO: creare un nuovo file di test per `vacation` ?
    def test_add_vacation(self):
        start = self.next_monday.replace(hour=10, minute=0)
        end = self.next_monday.replace(hour=11, minute=30)
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
        self.assertEqual(res.status_code, 201)

        res = self.api_session_anon.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": self.next_monday.replace(hour=10, minute=0).isoformat(),
                "booking_type": "Type A",
                "fields": [
                    {"name": "fullname", "value": "Mario Rossi"},
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
                "booking_date": self.next_monday.replace(
                    hour=10, minute=10
                ).isoformat(),
                "booking_type": "Type A",
                "fields": [
                    {"name": "fullname", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json(),
            {
                "error": {
                    "message": "Sorry, this slot is not available anymore.",
                    "type": "Bad Request",
                }
            },
        )
# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import timedelta

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.content.prenotazione import VACATION_TYPE
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


class TestBookingRestAPIAddBlock(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            required_booking_fields=["email"],
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.api_session.headers.update({"Accept": "application/json"})

    def test_anonymous_cant_add_block(self):
        self.api_session.auth = None
        booking_date = "{}T09:00:00+00:00".format(
            (date.today() + timedelta(1)).strftime("%Y-%m-%d")
        )
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": VACATION_TYPE,
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                ],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()["message"],
            f"You can't add a booking with type '{VACATION_TYPE}'.",
        )

    def test_manager_can_add_block_skipping_required_fields(self):
        booking_date = "{}T09:00:00+00:00".format(
            (date.today() + timedelta(1)).strftime("%Y-%m-%d")
        )
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": VACATION_TYPE,
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    # email is a required field from self.folder_prenotazioni schema
                ],
            },
        )
        self.assertEqual(res.status_code, 200)

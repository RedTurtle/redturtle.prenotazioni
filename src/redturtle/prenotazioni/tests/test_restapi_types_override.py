# -*- coding: utf-8 -*-
import unittest
from datetime import date

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestTypesOverrides(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

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
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")

        transaction.commit()

    def tearDown(self):
        self.api_session.close()

    def test_types_expanded_hide_prenotazioniyear(self):
        response = self.api_session.get(
            self.folder_prenotazioni.absolute_url(), params={"expand": "types"}
        )

        self.assertEqual(response.status_code, 200)
        res = response.json()
        prenotazioni_year = None
        for x in res["@components"]["types"]:
            if x["id"] == "PrenotazioniYear":
                prenotazioni_year = x
                break

        self.assertIsNotNone(prenotazioni_year)
        self.assertFalse(prenotazioni_year["immediately_addable"])
        self.assertFalse(prenotazioni_year["addable"])

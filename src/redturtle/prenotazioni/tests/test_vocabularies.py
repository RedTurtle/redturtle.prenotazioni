# -*- coding: utf-8 -*-
import unittest
from datetime import date

from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestVocabularies(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            same_day_booking_disallowed="no",
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
            duration=10,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        self.folder_prenotazioni_2 = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder 2",
            description="",
            daData=date.today(),
            gates=["Gate c", "Gate D"],
            same_day_booking_disallowed="no",
        )
        api.content.create(
            type="PrenotazioneType",
            title="Type C",
            duration=30,
            container=self.folder_prenotazioni_2,
            gates=["all"],
        )

    def tearDown(self):
        pass

    def test_booking_types(self):
        factory = getUtility(
            IVocabularyFactory, name="redturtle.prenotazioni.booking_types"
        )
        self.assertEqual(
            set(factory(self.portal).by_token.keys()), {"Type A", "Type B", "Type C"}
        )
        self.assertEqual(
            set(factory(self.folder_prenotazioni).by_token.keys()), {"Type A", "Type B"}
        )

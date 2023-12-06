# -*- coding: utf-8 -*-
import json
import unittest
from datetime import date

import transaction
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


class TestGatesOverrides(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "gates": ["Gate B", "foo", "bar"],
                        "to_day": "18",
                        "week_table": [],
                        "pause_table": [],
                    }
                ]
            ),
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

        self.view = api.content.get_view(
            name="prenotazioni_context_state",
            context=self.folder_prenotazioni,
            request=self.request,
        )

    def test_day_in_override_gates_return_overrided_gates_available_and_default_unavailable(
        self,
    ):
        now = date.today()
        gates = self.view.get_gates(date(now.year, 1, 10))
        self.assertEqual(
            gates,
            [
                {"name": "Gate A", "available": False},
                {"name": "Gate B", "available": True},
                {"name": "foo", "available": True},
                {"name": "bar", "available": True},
            ],
        )

    def test_day_not_in_override_gates(self):
        now = date.today()
        gates = self.view.get_gates(date(now.year, 6, 10))
        self.assertEqual(
            gates,
            [
                {"name": "Gate A", "available": True},
                {"name": "Gate B", "available": True},
            ],
        )

    def test_if_gates_override_not_set_use_default(self):
        folder = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            daData=date.today(),
            gates=["Gate A"],
            week_table=WEEK_TABLE_SCHEMA,
            week_table_overrides=json.dumps(
                [
                    {
                        "from_day": "1",
                        "from_month": "1",
                        "to_month": "2",
                        "pause_table": [],
                        "to_day": "18",
                        "week_table": [],
                        "gates": [],
                    }
                ]
            ),
        )
        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        view = api.content.get_view(
            name="prenotazioni_context_state",
            context=folder,
            request=self.request,
        )
        now = date.today()
        gates = view.get_gates(date(now.year, 1, 10))
        self.assertEqual(gates, [{"name": "Gate A", "available": True}])

# -*- coding: utf-8 -*-
import unittest
from datetime import date, datetime, timedelta

import transaction
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from freezegun import freeze_time
from redturtle.prenotazioni.adapters.booker import IBooker

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA

DATE_STR = "2023-12-05"  # because it's a monday


class TestGateChooser(unittest.TestCase):
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
            daData=date.today(),
            gates=["A", "B", "C", "D", "E"],
            week_table=WEEK_TABLE_SCHEMA,
        )

        api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=10,
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
        self.booker = IBooker(self.folder_prenotazioni)

    def create_booking(self, booking_date):
        # need this just to have the day container
        return self.booker.create(
            {
                "booking_date": booking_date,
                "booking_type": "Type A",
                "title": "foo",
            }
        )

    @freeze_time(DATE_STR)
    def test_when_all_gates_are_free_choose_one_randomly(self):
        now = datetime.fromisoformat(date.today().isoformat())
        available_gates = ["A", "B", "C", "D", "E"]
        used_gates = []
        first = self.create_booking(
            booking_date=now + timedelta(hours=9, minutes=0),
        )
        available_gates = [x for x in available_gates if x != first.gate]

        self.assertNotIn(first.gate, used_gates)
        self.assertNotIn(first.gate, available_gates)
        used_gates.append(first.gate)

        second = self.create_booking(
            booking_date=now + timedelta(hours=9, minutes=0),
        )
        available_gates = [x for x in available_gates if x != second.gate]
        self.assertNotIn(second.gate, used_gates)
        self.assertNotIn(second.gate, available_gates)
        used_gates.append(second.gate)

        third = self.create_booking(
            booking_date=now + timedelta(hours=9, minutes=0),
        )
        available_gates = [x for x in available_gates if x != third.gate]
        self.assertNotIn(third.gate, used_gates)
        self.assertNotIn(third.gate, available_gates)
        used_gates.append(third.gate)

        fourth = self.create_booking(
            booking_date=now + timedelta(hours=9, minutes=0),
        )
        available_gates = [x for x in available_gates if x != fourth.gate]
        self.assertNotIn(fourth.gate, used_gates)
        self.assertNotIn(fourth.gate, available_gates)
        used_gates.append(fourth.gate)

        fifth = self.create_booking(
            booking_date=now + timedelta(hours=9, minutes=0),
        )
        available_gates = [x for x in available_gates if x != fifth.gate]
        self.assertNotIn(fifth.gate, used_gates)
        self.assertNotIn(fifth.gate, available_gates)
        used_gates.append(fifth.gate)

        self.assertEqual(len(used_gates), 5)
        self.assertEqual(len(available_gates), 0)

        self.assertIsNone(
            self.create_booking(booking_date=now + timedelta(hours=9, minutes=0))
        )

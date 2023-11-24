# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import transaction
from Acquisition import aq_parent
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.autoform.interfaces import MODES_KEY
from plone.restapi.testing import RelativeSession
from zope.interface import Interface

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


class TestSchemaDirectives(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def test_field_modes(self):
        self.assertEqual(
            [
                (Interface, "booking_date", "display"),
                (Interface, "gate", "display"),
                (Interface, "booking_expiration_date", "display"),
                (Interface, "booking_code", "display"),
            ],
            IPrenotazione.queryTaggedValue(MODES_KEY),
        )


class TestBookingRestAPIInfo(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        self.api_session.close()

    def test_prenotazione_restapi_endpoint(self):
        result = self.api_session.get(self.portal_url + "/@types/Prenotazione")

        content_type_properties = result.json()["properties"]
        self.assertEqual(content_type_properties["booking_date"]["mode"], "display")
        self.assertEqual(content_type_properties["gate"]["mode"], "display")
        self.assertEqual(
            content_type_properties["booking_expiration_date"]["mode"],
            "display",
        )


class TestBookingRestAPIAdd(unittest.TestCase):
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
        )

        booking_type_A = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        api.content.transition(obj=booking_type_A, transition="publish")

        transaction.commit()

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.api_session.headers.update({"Accept": "application/json"})

    def test_add_booking_anonymous(self):
        self.api_session.auth = None
        booking_date = "{}T09:00:00+00:00".format(
            (date.today() + timedelta(1)).strftime("%Y-%m-%d")
        )
        booking_expiration_date = "{}T09:30:00+00:00".format(
            (date.today() + timedelta(1)).strftime("%Y-%m-%d")
        )
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": booking_date,
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["booking_date"], booking_date)
        self.assertEqual(res.json()["booking_expiration_date"], booking_expiration_date)
        self.assertEqual(res.json()["booking_type"], "Type A")
        self.assertIn(res.json()["gate"], ["Gate A", "Gate B"])
        self.assertEqual(res.json()["title"], "Mario Rossi")
        self.assertEqual(res.json()["email"], "mario.rossi@example")
        self.assertEqual(res.json()["id"], "mario-rossi")

    def test_add_booking_anonymous_wrong_booking_type(self):
        self.api_session.auth = None
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": "%sT09:00:00"
                % (date.today() + timedelta(1)).strftime("%Y-%m-%d"),
                "booking_type": "Type A (30 min)",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json(),
            {
                "message": "Unknown booking type 'Type A (30 min)'.",
                "type": "BadRequest",
            },
        )

    # def test_add_booking_auth(self):
    #     # TODO: testare anche con uno user non manager
    #     self.api_session.auth = (TEST_USER_NAME, TEST_USER_PASSWORD)

    def test_force_gate(self):
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": "%sT09:00:00"
                % (date.today() + timedelta(1)).strftime("%Y-%m-%d"),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
                "gate": "Gate A",
                "force": True,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["gate"], "Gate A")

    def test_force_gate_anonymous(self):
        self.api_session.auth = None
        res = self.api_session.post(
            self.folder_prenotazioni.absolute_url() + "/@booking",
            json={
                "booking_date": "%sT09:00:00"
                % (date.today() + timedelta(1)).strftime("%Y-%m-%d"),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                    {"name": "email", "value": "mario.rossi@example"},
                ],
                "gate": "Gate A",
                "force": True,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json(),
            {
                "message": "You are not allowed to force the gate.",
                "type": "BadRequest",
            },
        )

    def test_cant_add_booking_if_missing_required_fields(self):
        folder = api.content.create(
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
            container=folder,
            gates=["all"],
        )

        api.content.transition(obj=folder, transition="publish")
        transaction.commit()
        res = self.api_session.post(
            folder.absolute_url() + "/@booking",
            json={
                "booking_date": "%sT09:00:00"
                % (date.today() + timedelta(1)).strftime("%Y-%m-%d"),
                "booking_type": "Type A",
                "fields": [
                    {"name": "title", "value": "Mario Rossi"},
                ],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["message"], "Required input 'email' is missing.")


class TestPrenotazioniIntegrationTesting(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

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

    def test_booking_code_generation(self):
        booker = IBooker(self.folder_prenotazioni)

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=9
        )
        booking_expiration_date = datetime.fromisoformat(
            date.today().isoformat()
        ) + timedelta(days=1, hours=9, minutes=30)

        # need this just to have the day container
        container = aq_parent(
            booker.create(
                {
                    "booking_date": booking_date + timedelta(hours=5),
                    "booking_type": "Type A",
                    "title": "foo",
                }
            )
        )

        new_booking = api.content.create(
            container=container,
            type="Prenotazione",
            title="Booking A",
            booking_date=booking_date,
            gate="Gate A",
            booking_type="Type A",
            booking_expiration_date=booking_expiration_date,
        )
        self.assertIsNot(new_booking.getBookingCode(), None)
        self.assertTrue(len(new_booking.getBookingCode()) > 0)

    def test_booking_code_uniqueness(self):
        booker = IBooker(self.folder_prenotazioni)

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=9
        )
        booking_expiration_date = datetime.fromisoformat(
            date.today().isoformat()
        ) + timedelta(days=1, hours=9, minutes=30)

        # need this just to have the day container
        container = aq_parent(
            booker.create(
                {
                    "booking_date": booking_date + timedelta(hours=5),
                    "booking_type": "Type A",
                    "title": "foo",
                }
            )
        )

        booking_gate_A = api.content.create(
            container=container,
            type="Prenotazione",
            title="Booking A",
            booking_date=booking_date,
            gate="Gate A",
            booking_type="Type A",
            booking_expiration_date=booking_expiration_date,
        )
        booking_gate_B = api.content.create(
            container=container,
            type="Prenotazione",
            title="Booking B",
            booking_date=booking_date,
            gate="Gate B",
            booking_type="Type A",
            booking_expiration_date=booking_expiration_date,
        )

        self.assertNotEqual(
            booking_gate_A.getBookingCode(), booking_gate_B.getBookingCode()
        )

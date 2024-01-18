# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import transaction
from freezegun import freeze_time
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.autoform.interfaces import MODES_KEY
from plone.restapi.testing import RelativeSession
from zope.interface import Interface

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.exceptions.booker import BookerException
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA

DATE_STR = "2023-05-14"


class Mixin(unittest.TestCase):
    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal_url = self.portal.absolute_url()

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )

        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
        )

        type_a = api.content.create(
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

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")


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

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )

        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])

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

    def tearDown(self):
        self.api_session.close()
        self.folder_prenotazioni.auto_confirm_manager = False

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

    def test_auto_confirm_manager_false_does_nothing(self):
        self.folder_prenotazioni.auto_confirm_manager = False
        transaction.commit()
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
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["booking_status"], "pending")

    def test_auto_confirm_manager_admin(self):
        self.folder_prenotazioni.auto_confirm_manager = True
        transaction.commit()
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
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["booking_status"], "confirmed")

    def test_auto_confirm_manager_gestore(self):
        self.folder_prenotazioni.auto_confirm_manager = True
        transaction.commit()

        api_session = RelativeSession(self.portal_url)
        api_session.auth = ("jdoe", "secret!!!")
        api_session.headers.update({"Accept": "application/json"})

        res = api_session.post(
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
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["booking_status"], "confirmed")

    def test_auto_confirm_manager_anon_does_nothing(self):
        self.folder_prenotazioni.auto_confirm_manager = True
        transaction.commit()

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
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["booking_status"], "pending")


class TestPrenotazioniIntegrationTesting(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.portal_url = self.portal.absolute_url()

        api.user.create(
            email="user@example.com",
            username="jdoe",
            password="secret!!!",
        )

        api.user.grant_roles(username="jdoe", roles=["Bookings Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

    def create_booking(self, data: dict):
        booker = IBooker(self.folder_prenotazioni)
        return booker.book(data)

    def test_booking_code_generation(self):
        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = self.create_booking(
            {
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        self.assertIsNot(booking.getBookingCode(), None)
        self.assertTrue(len(booking.getBookingCode()) > 0)

    def test_booking_code_uniqueness(self):
        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking_1 = self.create_booking(
            {
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            }
        )

        booking_2 = self.create_booking(
            {
                "booking_date": booking_date + timedelta(hours=1, minutes=30),
                "booking_type": "Type A",
                "title": "foo 2",
            }
        )

        self.assertNotEqual(booking_1.getBookingCode(), booking_2.getBookingCode())

    def test_booker_auto_confirm_manager_true_by_default(self):
        folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        booker = IBooker(folder_prenotazioni)

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = booker.book(
            data={
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            }
        )

        self.assertEqual(api.content.get_state(obj=booking), "confirmed")

    def test_booker_auto_confirm_manager_does_nothing_if_false(self):
        folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm_manager=False,
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        booker = IBooker(folder_prenotazioni)

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = booker.book(
            data={
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            },
        )

        self.assertEqual(api.content.get_state(obj=booking), "pending")

    def test_booker_auto_confirm_manager_called_by_admin(self):
        folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm_manager=True,
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        booker = IBooker(folder_prenotazioni)

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = booker.book(
            data={
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            },
        )

        self.assertEqual(api.content.get_state(obj=booking), "confirmed")

    def test_booker_auto_confirm_manager_called_by_gestore(self):
        folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm_manager=True,
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        booker = IBooker(folder_prenotazioni)

        login(self.portal, "jdoe")

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = booker.book(
            data={
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            },
        )

        self.assertEqual(api.content.get_state(obj=booking), "confirmed")

    def test_booker_auto_confirm_manager_called_by_anon_does_nothing(self):
        folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm_manager=True,
        )

        type_a = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=folder_prenotazioni,
            gates=["all"],
        )
        api.content.transition(obj=folder_prenotazioni, transition="publish")
        api.content.transition(obj=type_a, transition="publish")

        booker = IBooker(folder_prenotazioni)

        logout()

        booking_date = datetime.fromisoformat(date.today().isoformat()) + timedelta(
            days=1, hours=8
        )
        booking = booker.book(
            data={
                "booking_date": booking_date + timedelta(hours=1),
                "booking_type": "Type A",
                "title": "foo",
            },
        )

        self.assertEqual(api.content.get_state(obj=booking), "pending")

    @freeze_time(DATE_STR)  # far from holidays
    def test_booker_disallow_anon_creation_if_futureDays_is_set_and_passed(self):
        today = date.today()
        self.folder_prenotazioni.daData = today
        self.folder_prenotazioni.futureDays = 6

        logout()

        with self.assertRaises(BookerException) as cm:
            self.create_booking(
                data={
                    "booking_date": datetime.fromisoformat(today.isoformat())
                    + timedelta(hours=8, days=8),
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                }
            )
        self.assertEqual(
            "Sorry, you can not book this slot for now.", str(cm.exception)
        )

        # but can create a book inside range
        future_date = datetime.fromisoformat(today.isoformat()) + timedelta(
            hours=8, days=5
        )
        book = self.create_booking(
            data={
                "booking_date": future_date,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )
        self.assertEqual(book.booking_date.date(), future_date.date())

    @freeze_time(DATE_STR)  # far from holidays
    def test_booker_bypass_futureDays_check_if_manager(self):
        today = date.today()
        self.folder_prenotazioni.daData = today
        self.folder_prenotazioni.futureDays = 6

        logout()
        login(self.portal, "jdoe")

        future_date = datetime.fromisoformat(today.isoformat()) + timedelta(
            hours=8, days=8
        )
        book = self.create_booking(
            data={
                "booking_date": future_date,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )
        self.assertEqual(book.booking_date.date(), future_date.date())

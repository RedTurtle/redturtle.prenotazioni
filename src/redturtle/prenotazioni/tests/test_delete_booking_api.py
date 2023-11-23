# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import transaction
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.restapi.testing import RelativeSession

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestDeleteBookingApi(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        api.user.create(
            email="user@example.com",
            username="user",
            password="secret!!!",
        )
        api.user.create(
            email="user@example.com",
            username="user2",
            password="secret!!!",
        )

        self.api_session_admin = RelativeSession(self.portal_url)
        self.api_session_admin.headers.update({"Accept": "application/json"})
        self.api_session_admin.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        self.api_session_anon = RelativeSession(self.portal_url)
        self.api_session_anon.headers.update({"Accept": "application/json"})

        self.api_session_user = RelativeSession(self.portal_url)
        self.api_session_user.headers.update({"Accept": "application/json"})
        self.api_session_user.auth = ("user", "secret!!!")

        self.api_session_user2 = RelativeSession(self.portal_url)
        self.api_session_user2.headers.update({"Accept": "application/json"})
        self.api_session_user2.auth = ("user2", "secret!!!")

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
            gates=["Gate A"],
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

        self.view = api.content.get_view(
            name="confirm-delete",
            context=self.folder_prenotazioni,
            request=self.request,
        )
        self.booker = IBooker(self.folder_prenotazioni)
        self.today = datetime.now().replace(hour=8, microsecond=0)

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

    def tearDown(self):
        if "uid" in self.request.form:
            del self.request.form["uid"]

        self.api_session_admin.close()
        self.api_session_anon.close()
        self.api_session_user.close()
        self.api_session_user2.close()

    def get_response(self, session, uid=None):
        if not uid:
            response = session.delete("{}/@booking".format(self.portal_url))
        else:
            response = session.delete("{}/@booking/{}".format(self.portal_url, uid))
        # per le restapi il commit qui non ha senso, senza i test si rompono,
        # ma è un caso, va spostato dove serve veramente, questo non è il suo posto
        transaction.commit()
        return response

    def test_endpoint_raise_404_without_uid(self):
        response = self.get_response(session=self.api_session_admin)
        self.assertEqual(404, response.status_code)

    def test_view_raise_404_with_wrong_uid(self):
        response = self.get_response(session=self.api_session_admin, uid="foo")
        self.assertEqual(404, response.status_code)

    def test_admin_can_delete_booking(self):
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertIsNotNone(api.content.get(UID=uid))

        response = self.get_response(session=self.api_session_admin, uid=uid)
        transaction.commit()

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(api.content.get(UID=uid))

    @unittest.skip("wip")
    def test_anon_cant_delete_other_user_booking(self):
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertIsNotNone(api.content.get(UID=uid))

        response = self.get_response(session=self.api_session_anon, uid=uid)

        self.assertEqual(response.status_code, 401)
        self.assertIsNotNone(api.content.get(UID=uid))

    def test_anon_can_delete_anon_booking(self):
        logout()
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_anon, uid=uid)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            0,
        )

    def test_user_can_delete_his_booking(self):
        login(self.portal, "user")
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_user, uid=uid)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            0,
        )

    @unittest.skip("wip")
    def test_user_cant_delete_other_user_booking(self):
        login(self.portal, "user")
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_user2, uid=uid)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    @unittest.skip("wip")
    def test_user_cant_delete_anon_booking(self):
        logout()
        booking = self.booker.create(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_user, uid=uid)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    def test_cant_delete_past_booking(self):
        booking = self.booker.create(
            {
                "booking_date": self.today - timedelta(1),  # yesterday
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_admin, uid=uid)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            "You can't delete your reservation; it's too late.",
            response.json()["message"],
        )
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    def test_cant_delete_today_booking(self):
        booking = self.booker.create(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        response = self.get_response(session=self.api_session_admin, uid=uid)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            "You can't delete your reservation; it's too late.",
            response.json()["message"],
        )
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

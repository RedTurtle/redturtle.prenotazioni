# -*- coding: utf-8 -*-
from .helpers import WEEK_TABLE_SCHEMA
from datetime import date
from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

import transaction
import unittest


class TestCleanupPendingBookingsApi(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today() - timedelta(days=365),
            gates=["Gate A"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm=False,
            auto_confirm_manager=False,
        )
        self.folder.pending_bookings_cleanup_enabled = True
        self.folder.pending_bookings_cleanup_days = 5
        self.folder.pending_bookings_cleanup_delete = False
        self.folder.pending_bookings_cleanup_notify_users = False

        booking_type = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder,
            gates=["all"],
        )

        api.content.transition(obj=self.folder, transition="publish")
        api.content.transition(obj=booking_type, transition="publish")
        transaction.commit()

        self.api_session = RelativeSession(self.portal.absolute_url())
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        self.api_session.close()

    @freeze_time("2026-04-10 10:00:00")
    def _create_old_pending_booking(self):
        booking = IBooker(self.folder).book(
            {
                "booking_date": datetime(2026, 4, 11, 10, 0, 0),
                "booking_type": "Type A",
                "title": "Booking",
                "email": "jdoe@example.com",
            }
        )
        transaction.commit()
        return booking

    def _get_booking_status(self, uid):
        res = self.api_session.get(self.portal.absolute_url() + f"/@booking/{uid}")
        self.assertEqual(res.status_code, 200)
        return res.json()["booking_status"]

    def test_get_endpoint_is_dry_run(self):
        booking = self._create_old_pending_booking()
        uid = booking.UID()
        self.assertEqual(self._get_booking_status(uid), "pending")

        res = self.api_session.get(
            self.portal.absolute_url() + "/@cleanup-pending-bookings"
        )

        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["stats"]["matched"], 1)
        self.assertEqual(self._get_booking_status(uid), "pending")

    def test_post_endpoint_executes_cleanup(self):
        booking = self._create_old_pending_booking()
        uid = booking.UID()
        self.assertEqual(self._get_booking_status(uid), "pending")

        res = self.api_session.post(
            self.portal.absolute_url() + "/@cleanup-pending-bookings"
        )

        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertFalse(payload["dry_run"])
        self.assertEqual(payload["stats"]["canceled"], 1)
        self.assertEqual(self._get_booking_status(uid), "canceled")

    def test_folder_scope_endpoint(self):
        booking = self._create_old_pending_booking()
        uid = booking.UID()

        res = self.api_session.post(
            self.folder.absolute_url() + "/@cleanup-pending-bookings"
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["scope"], "folder")
        self.assertEqual(self._get_booking_status(uid), "canceled")

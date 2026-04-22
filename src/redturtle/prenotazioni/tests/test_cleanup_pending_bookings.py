# -*- coding: utf-8 -*-
from .helpers import WEEK_TABLE_SCHEMA
from datetime import date
from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from redturtle.prenotazioni.utilities.pending_cleanup import (
    cleanup_pending_bookings_in_site,
)

import unittest


class TestCleanupPendingBookings(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
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
        self.folder_prenotazioni.pending_bookings_cleanup_enabled = True
        self.folder_prenotazioni.pending_bookings_cleanup_days = 5

        self.booking_type = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        api.content.transition(obj=self.booking_type, transition="publish")

    @freeze_time("2026-04-10 10:00:00")
    def _create_old_pending_booking(self, email="jdoe@example.com"):
        booking = IBooker(self.folder_prenotazioni).book(
            {
                "booking_date": datetime(2026, 4, 11, 10, 0, 0),
                "booking_type": "Type A",
                "title": "Booking",
                "email": email,
            }
        )
        return booking

    def test_cleanup_moves_old_pending_to_canceled_and_notifies_user(self):
        self.folder_prenotazioni.pending_bookings_cleanup_delete = False
        self.folder_prenotazioni.pending_bookings_cleanup_notify_users = True

        booking = self._create_old_pending_booking()
        self.assertEqual(api.content.get_state(obj=booking), "pending")

        result = cleanup_pending_bookings_in_site()

        self.assertEqual(result["canceled"], 1)
        self.assertEqual(result["deleted"], 0)
        self.assertEqual(api.content.get_state(obj=booking), "canceled")

        self.assertEqual(len(self.mailhost.messages), 1)
        self.assertIn(
            b"Subject: [Prenota foo] Booking canceled", self.mailhost.messages[0]
        )

    def test_cleanup_deletes_old_pending_without_notifications(self):
        self.folder_prenotazioni.pending_bookings_cleanup_delete = True
        self.folder_prenotazioni.pending_bookings_cleanup_notify_users = False

        booking = self._create_old_pending_booking()
        uid = booking.UID()
        self.assertIsNotNone(api.content.get(UID=uid))

        result = cleanup_pending_bookings_in_site()

        self.assertEqual(result["deleted"], 1)
        self.assertIsNone(api.content.get(UID=uid))
        self.assertEqual(len(self.mailhost.messages), 0)

    def test_cleanup_dry_run_does_not_change_state(self):
        booking = self._create_old_pending_booking()
        self.assertEqual(api.content.get_state(obj=booking), "pending")

        result = cleanup_pending_bookings_in_site(dry_run=True)

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["canceled"], 1)
        self.assertEqual(api.content.get_state(obj=booking), "pending")

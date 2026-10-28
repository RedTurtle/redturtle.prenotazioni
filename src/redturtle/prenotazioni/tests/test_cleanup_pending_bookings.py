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
from redturtle.prenotazioni.scripts.cleanup_pending_bookings import (
    cleanup_pending_bookings_in_site,
)
from redturtle.prenotazioni.scripts.cleanup_pending_bookings import main
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from unittest import mock

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


class TestCleanupPendingBookingsScript(unittest.TestCase):
    """Tests for the main() entry point in cleanup_pending_bookings script."""

    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota script test",
            description="",
            daData=date.today() - timedelta(days=365),
            gates=["Gate A"],
            week_table=WEEK_TABLE_SCHEMA,
            auto_confirm=False,
            auto_confirm_manager=False,
        )
        self.folder_prenotazioni.pending_bookings_cleanup_enabled = True
        self.folder_prenotazioni.pending_bookings_cleanup_days = 5
        self.folder_prenotazioni.pending_bookings_cleanup_delete = False
        self.folder_prenotazioni.pending_bookings_cleanup_notify_users = False

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
    def _create_old_pending_booking(self):
        return IBooker(self.folder_prenotazioni).book(
            {
                "booking_date": datetime(2026, 4, 11, 10, 0, 0),
                "booking_type": "Type A",
                "title": "Booking",
                "email": "jdoe@example.com",
            }
        )

    def _folder_path(self):
        return "/".join(self.folder_prenotazioni.getPhysicalPath())

    @mock.patch("redturtle.prenotazioni.scripts.cleanup_pending_bookings.commit")
    def test_main_whole_site_no_commit_by_default(self, mock_commit):
        booking = self._create_old_pending_booking()
        with mock.patch("sys.argv", ["script"]):
            main()
        mock_commit.assert_not_called()
        self.assertEqual(api.content.get_state(obj=booking), "canceled")

    @mock.patch("redturtle.prenotazioni.scripts.cleanup_pending_bookings.commit")
    def test_main_with_commit_flag_commits(self, mock_commit):
        self._create_old_pending_booking()
        with mock.patch("sys.argv", ["script", "--commit"]):
            main()
        mock_commit.assert_called_once()

    @mock.patch("redturtle.prenotazioni.scripts.cleanup_pending_bookings.commit")
    def test_main_with_path_processes_only_that_folder(self, mock_commit):
        booking = self._create_old_pending_booking()
        with mock.patch("sys.argv", ["script", "--path", self._folder_path()]):
            main()
        mock_commit.assert_not_called()
        self.assertEqual(api.content.get_state(obj=booking), "canceled")

    @mock.patch("redturtle.prenotazioni.scripts.cleanup_pending_bookings.commit")
    def test_main_with_nonexistent_path_logs_error_and_returns(self, mock_commit):
        with mock.patch("sys.argv", ["script", "--path", "/nonexistent/path"]):
            with self.assertLogs("redturtle.prenotazioni", level="ERROR") as cm:
                main()
        mock_commit.assert_not_called()
        self.assertTrue(any("No object found" in line for line in cm.output))

    @mock.patch("redturtle.prenotazioni.scripts.cleanup_pending_bookings.commit")
    def test_main_with_path_to_wrong_type_logs_error_and_returns(self, mock_commit):
        # Use the portal itself (not a PrenotazioniFolder) as the wrong-type object
        portal_path = "/".join(self.portal.getPhysicalPath())
        with mock.patch("sys.argv", ["script", "--path", portal_path]):
            with self.assertLogs("redturtle.prenotazioni", level="ERROR") as cm:
                main()
        mock_commit.assert_not_called()
        self.assertTrue(
            any("is not a PrenotazioniFolder" in line for line in cm.output)
        )

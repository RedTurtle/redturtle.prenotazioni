# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from datetime import date
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from zExceptions import NotFound

import transaction
import unittest


class TestDeleteBooking(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.mailhost = self.portal.MailHost

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

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
            gates=["Gate A"],
            email_responsabile=["operator@example.org"],
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
        self.today = datetime.now().replace(hour=8)

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

    def tearDown(self):
        if "uid" in self.request.form:
            del self.request.form["uid"]

    def test_view_raise_404_without_uid(self):
        self.assertRaises(NotFound, self.view.do_delete)

    def test_view_raise_404_with_wrong_uid(self):
        self.request.form["uid"] = "foo"
        self.assertRaises(NotFound, self.view.do_delete)

    def test_admin_can_delete_booking(self):
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        self.assertIsNotNone(api.content.get(UID=uid))
        # creation email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 1)

        self.request.form["uid"] = booking.UID()
        res = self.view.do_delete()
        self.assertIsNone(res)
        self.assertEqual(api.content.get_state(api.content.get(UID=uid)), "canceled")

        # cancel email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 2)
        # XXX: we should check the email destination, but actually we can't,
        # because MockMailHost doesn't store the bcc field
        self.assertIn(b"Subject: Booking canceled: ", self.mailhost.messages[1])

    @unittest.skip("wip")
    def test_anon_cant_delete_other_user_booking(self):
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        self.assertIsNotNone(api.content.get(UID=uid))

        logout()

        self.request.form["uid"] = booking.UID()
        self.assertRaises(Unauthorized, self.view.do_delete)

    def test_anon_can_delete_anon_booking(self):
        logout()
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )
        # creation email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 1)

        self.request.form["uid"] = booking.UID()
        res = self.view.do_delete()

        self.assertIsNone(res)
        # the booking is marked as canceled
        brains = self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)
        self.assertEqual([brain.review_state for brain in brains], ["canceled"])

        # cancel email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 2)
        # XXX: we should check the email destination, but actually we can't,
        # because MaockMailHost doesn't store the bcc field
        self.assertIn(b"Subject: Booking canceled: ", self.mailhost.messages[1])

    def test_user_can_delete_his_booking(self):
        login(self.portal, "user")
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        # creation email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 1)

        self.request.form["uid"] = booking.UID()
        res = self.view.do_delete()

        self.assertIsNone(res)
        # the booking is marked as canceled
        brains = self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)
        self.assertEqual([brain.review_state for brain in brains], ["canceled"])

        # cancel email is sent to the operator
        self.assertEqual(len(self.mailhost.messages), 2)
        # XXX: we should check the email destination, but actually we can't,
        # because MaockMailHost doesn't store the bcc field
        self.assertIn(b"Subject: Booking canceled: ", self.mailhost.messages[1])

    @unittest.skip("wip")
    def test_user_cant_delete_other_user_booking(self):
        login(self.portal, "user")
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        login(self.portal, "user2")
        uid = booking.UID()
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        self.request.form["uid"] = booking.UID()

        self.assertRaises(Unauthorized, self.view.do_delete)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    @unittest.skip("wip")
    def test_user_cant_delete_anon_booking(self):
        logout()
        booking = self.booker.book(
            {
                "booking_date": self.today + timedelta(1),  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        login(self.portal, "user")
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        self.request.form["uid"] = booking.UID()

        self.assertRaises(Unauthorized, self.view.do_delete)
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    def test_cant_delete_past_booking(self):
        booking = self.booker.book(
            {
                "booking_date": self.today - timedelta(1),  # yesterday
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        self.request.form["uid"] = booking.UID()
        res = self.view.do_delete()

        self.assertEqual(
            "You can't delete your reservation; it's too late.", res["error"]
        )
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    def test_cant_delete_today_booking(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        self.request.form["uid"] = booking.UID()
        res = self.view.do_delete()

        self.assertEqual(
            "You can't delete your reservation; it's too late.", res["error"]
        )
        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

    def test_unable_to_delete_other_types(self):
        document = api.content.create(
            container=self.portal,
            type="Document",
            title="Document",
        )
        uid = document.UID()
        api.content.transition(obj=document, transition="publish")
        transaction.commit()

        self.assertIsNotNone(api.content.get(UID=uid))

        self.request.form["uid"] = uid
        self.assertRaises(NotFound, self.view.do_delete)

        self.assertIsNotNone(api.content.get(UID=uid))

    def test_can_delete_today_booking_if_it_is_block(self):
        booking = self.booker.book(
            {
                "booking_date": self.today,
                "booking_type": "out-of-office",
                "title": "foo",
            }
        )
        uid = booking.UID()

        self.assertEqual(
            len(self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)),
            1,
        )

        self.request.form["uid"] = booking.UID()

        self.view.do_delete()

        self.assertEqual(
            self.portal.portal_catalog.unrestrictedSearchResults(UID=uid)[
                0
            ].review_state,
            "canceled",
        )

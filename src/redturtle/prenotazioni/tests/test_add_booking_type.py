# -*- coding: utf-8 -*-
from AccessControl.unauthorized import Unauthorized
from datetime import date
from datetime import time
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import unittest


class TestAddBookingType(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

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

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            gates=["Gate A", "Gate B"],
            week_table=WEEK_TABLE_SCHEMA,
        )

    def test_booking_manager_cant_add_types(self):
        login(self.portal, "jdoe")

        self.assertRaises(
            Unauthorized,
            api.content.create,
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

    def test_contributor_can_add_types(self):
        api.user.grant_roles(username="jdoe", roles=["Bookings Manager", "Contributor"])
        login(self.portal, "jdoe")

        obj = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        self.assertEqual(obj.getId(), "type-a")

    def test_duration_autoset_from_time_range_on_create(self):
        obj = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            container=self.folder_prenotazioni,
            gates=["all"],
            start_time=time(9, 0),
            end_time=time(10, 30),
        )

        self.assertEqual(obj.duration, "90")

    def test_duration_autoset_from_time_range_on_edit(self):
        obj = api.content.create(
            type="PrenotazioneType",
            title="Type A",
            duration=30,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        obj.start_time = time(11, 0)
        obj.end_time = time(12, 15)
        notify(ObjectModifiedEvent(obj))

        self.assertEqual(obj.duration, "75")

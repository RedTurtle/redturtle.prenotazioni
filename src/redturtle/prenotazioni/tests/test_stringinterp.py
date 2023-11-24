# -*- coding: UTF-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.stringinterp.interfaces import IStringSubstitution
from zope.component import getAdapter

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


class TestStringInterp(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    maxDiff = None
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.today_8_0 = self.dt_local_to_utc(
            datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        )
        self.tomorrow_8_0 = self.today_8_0 + timedelta(1)

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
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
        for data in week_table:
            data["morning_start"] = "0700"
            data["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        api.portal.set_registry_record(
            "plone.portal_timezone",
            self.timezone,
        )

    def test_stringinterp(self):
        booker = IBooker(self.folder_prenotazioni)
        booking = booker.create(
            {
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )
        booking_print_url = getAdapter(
            booking, IStringSubstitution, "booking_print_url"
        )()
        self.assertEqual(
            booking_print_url,
            f"http://nohost/plone/prenota-foo/@@prenotazione_print?uid={booking.UID()}",
        )

        # plone localized date
        # booking_date = getAdapter(booking, IStringSubstitution, "booking_date")()
        # booking_end_date = getAdapter(booking, IStringSubstitution, "booking_end_date")()

        # localized time
        booking_time = getAdapter(booking, IStringSubstitution, "booking_time")()
        booking_time_end = getAdapter(
            booking, IStringSubstitution, "booking_time_end"
        )()
        self.assertEqual(booking_time, "08:00")
        self.assertEqual(booking_time_end, "08:30")

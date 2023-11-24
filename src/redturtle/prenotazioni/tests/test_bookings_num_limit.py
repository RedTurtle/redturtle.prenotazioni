# -*- coding: UTF-8 -*-
import unittest
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytz
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.exceptions import BookingsLimitExceded
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestEmailToManagers(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    timezone = "Europe/Rome"

    def dt_local_to_utc(self, value):
        return pytz.timezone(self.timezone).localize(value).astimezone(pytz.utc)

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        self.testing_fiscalcode = "TESTINGFISCALCODE"

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
        api.content.create(
            type="PrenotazioneType",
            title="Type B",
            duration=90,
            container=self.folder_prenotazioni,
            gates=["all"],
        )

        week_table = self.folder_prenotazioni.week_table
        for data in week_table:
            data["morning_start"] = "0700"
            data["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        self.today_8_0 = self.dt_local_to_utc(
            datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        )
        self.tomorrow_8_0 = self.today_8_0 + timedelta(1)
        self.folder_prenotazioni.email_responsabile = ["admin@test.com"]
        api.portal.set_registry_record(
            "plone.portal_timezone",
            self.timezone,
        )

    def create_booking(self, data: dict):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(data)

    def test_limit_exceeded_raises_exception(self):
        self.folder_prenotazioni.max_bookings_allowed = 1

        self.create_booking(
            data={
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        self.assertRaises(
            BookingsLimitExceded,
            self.create_booking,
            data={
                "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            },
        )

    def test_limit_exceeded_raises_exception_on_preserved_fiscalcode(self):
        self.folder_prenotazioni.max_bookings_allowed = 1
        fiscalcode = "FISCALCODETESTER"

        tester = api.user.create(email="tester@tester.com", username=fiscalcode)

        with api.env.adopt_user(user=tester):
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0,
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                },
            )

            self.assertRaises(
                BookingsLimitExceded,
                self.create_booking,
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                },
            )

    def test_limit_exceeded_is_not_raised_if_limit_0(self):
        self.create_booking(
            data={
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        self.assertTrue(
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                    "fiscalcode": self.testing_fiscalcode,
                }
            )
        )

    def test_limit_exceeded_is_not_raised_if_have_the_past_bookings(self):
        self.folder_prenotazioni.max_bookings_allowed = 1
        self.create_booking(
            data={
                "booking_date": self.today_8_0 - timedelta(days=1),
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        self.assertTrue(
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                    "fiscalcode": self.testing_fiscalcode,
                }
            )
        )

    def test_limit_exceeded_is_not_raised_if_have_refused_bookings(self):
        self.folder_prenotazioni.max_bookings_allowed = 1

        booking = self.create_booking(
            data={
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        api.content.transition(obj=booking, transition="refuse")
        booking.reindexObject(idxs=["review_state"])

        self.assertTrue(
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "Type A",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                    "fiscalcode": self.testing_fiscalcode,
                }
            )
        )

    def test_limit_exceeded_is_not_raised_if_different_booking_type(self):
        self.create_booking(
            data={
                "booking_date": self.tomorrow_8_0,
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        self.assertTrue(
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "Type B",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                    "fiscalcode": self.testing_fiscalcode,
                }
            )
        )

    def test_limit_exceeded_not_raised_if_type_is_out_of_office(self):
        self.folder_prenotazioni.max_bookings_allowed = 1

        self.create_booking(
            data={
                "booking_date": self.tomorrow_8_0,
                "booking_type": "out-of-office",
                "title": "foo",
                "email": "jdoe@redturtle.it",
                "fiscalcode": self.testing_fiscalcode,
            }
        )

        self.assertTrue(
            self.create_booking(
                data={
                    "booking_date": self.tomorrow_8_0 + timedelta(days=1),
                    "booking_type": "out-of-office",
                    "title": "foo",
                    "email": "jdoe@redturtle.it",
                    "fiscalcode": self.testing_fiscalcode,
                },
            )
        )

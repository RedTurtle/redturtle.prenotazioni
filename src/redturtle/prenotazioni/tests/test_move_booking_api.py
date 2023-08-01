# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from datetime import timedelta
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


class TestMoveBookingApi(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session_admin = RelativeSession(self.portal_url)
        self.api_session_admin.headers.update({"Accept": "application/json"})
        self.api_session_admin.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        self.portal_url = self.portal.absolute_url()
        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Folder",
            description="",
            daData=date.today(),
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
        )
        week_table = self.folder_prenotazioni.week_table
        for row in week_table:
            row["morning_start"] = "0700"
            row["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        self.booker = IBooker(self.folder_prenotazioni)
        self.today = datetime.now().replace(hour=8, microsecond=0)

        api.content.transition(obj=self.folder_prenotazioni, transition="publish")
        transaction.commit()

    def tearDown(self):
        self.api_session_admin.close()

    def get_response(self, session, uid=None):
        if not uid:
            response = session.delete("{}/@booking".format(self.portal_url))
        else:
            response = session.delete("{}/@booking/{}".format(self.portal_url, uid))
        # per le restapi il commit qui non ha senso, senza i test si rompono,
        # ma è un caso, va spostato dove serve veramente, questo non è il suo posto
        transaction.commit()
        return response

    def test_move_booking(self):
        booking = self.booker.create(
            {
                "booking_date": self.today,
                "booking_type": "Type A",
                "title": "foo",
            }
        )
        uid = booking.UID()
        transaction.commit()

        tomorrow = self.today + timedelta(1)
        response = self.api_session_admin.post(
            f"{self.folder_prenotazioni.absolute_url()}/@booking-move",
            json={
                "booking_id": uid,
                "booking_date": tomorrow.isoformat(),  # tomorrow
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.api_session_admin.get(
            f"{self.folder_prenotazioni.absolute_url()}/@booking/{uid}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            datetime.fromisoformat(response.json()["booking_date"]),
            tomorrow,
        )

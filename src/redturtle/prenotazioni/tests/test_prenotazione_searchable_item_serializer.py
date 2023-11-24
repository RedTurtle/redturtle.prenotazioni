# -*- coding: utf-8 -*-
import unittest
from datetime import date
from datetime import timedelta

from dateutil import parser
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.serializer.converters import json_compatible
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.i18n import translate

from redturtle.prenotazioni.interfaces import ISerializeToPrenotazioneSearchableItem
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING


class TestPrenotazioniSearch(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
    maxDiff = None

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.testing_fiscal_code = "TESTINGFISCALCODE"
        self.testing_booking_date = parser.parse("2023-04-28 16:00:00")
        self.booking_expiration_date = parser.parse("2023-04-28 16:00:00") + timedelta(
            days=100
        )
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
        week_table[0]["morning_start"] = "0700"
        week_table[0]["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

        year = api.content.create(
            container=self.folder_prenotazioni,
            type="PrenotazioniYear",
            title="Year",
        )
        week = api.content.create(container=year, type="PrenotazioniWeek", title="Week")
        self.day_folder = api.content.create(
            container=week, type="PrenotazioniDay", title="Day"
        )

        self.prenotazione_fscode = api.content.create(
            container=self.day_folder,
            type="Prenotazione",
            title="Prenotazione",
            booking_date=self.testing_booking_date - timedelta(days=2),
            booking_expiration_date=self.booking_expiration_date,
            fiscalcode=self.testing_fiscal_code,
        )

    def test_serializer_fields(self):
        result = getMultiAdapter(
            (self.prenotazione_fscode, getRequest()),
            ISerializeToPrenotazioneSearchableItem,
        )()
        wf_tool = api.portal.get_tool("portal_workflow")
        status = wf_tool.getStatusOf("prenotazioni_workflow", self.prenotazione_fscode)
        self.assertEqual(
            result,
            {
                "title": self.prenotazione_fscode.Title(),
                "description": self.prenotazione_fscode.Description(),
                "booking_id": self.prenotazione_fscode.UID(),
                "booking_code": self.prenotazione_fscode.getBookingCode(),
                "booking_url": self.prenotazione_fscode.absolute_url(),
                "booking_date": json_compatible(self.prenotazione_fscode.booking_date),
                "booking_expiration_date": json_compatible(
                    self.prenotazione_fscode.booking_expiration_date
                ),
                "booking_type": self.prenotazione_fscode.booking_type,
                # "booking_room": "stanza-1",
                "booking_gate": self.prenotazione_fscode.gate,
                "booking_status": status["review_state"],
                "booking_status_label": translate(
                    status["review_state"], context=getRequest()
                ),
                "booking_status_date": json_compatible(status["time"]),
                "booking_status_notes": status["comments"],
                "fiscalcode": self.prenotazione_fscode.fiscalcode,
                # 'cosa_serve': None,
                # 'description': '',
                "email": self.prenotazione_fscode.email,
                # 'gate': None,
                # 'id': 'prenotazione',
                "phone": self.prenotazione_fscode.phone,
                "staff_notes": self.prenotazione_fscode.staff_notes,
                "company": self.prenotazione_fscode.company,
                "vacation": None,
            },
        )

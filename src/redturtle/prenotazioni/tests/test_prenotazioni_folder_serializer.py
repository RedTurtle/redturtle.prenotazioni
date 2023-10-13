# -*- coding: UTF-8 -*-
import unittest
from datetime import date

from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from redturtle.prenotazioni.tests.helpers import WEEK_TABLE_SCHEMA


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestPrenotazioniFolderSerializer(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        self.hidden_type_name = "Type Hidden"
        self.not_hidden_type_name = "Type visible"

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            booking_types=[
                {
                    "name": self.hidden_type_name,
                    "duration": "30",
                    "hidden": True,
                },
                {
                    "name": self.not_hidden_type_name,
                    "duration": "30",
                    "hidden": False,
                },
            ],
            gates=["Gate A"],
        )
        self.folder_prenotazioni.week_table = WEEK_TABLE_SCHEMA

        setRoles(self.portal, TEST_USER_ID, ["User"])

    def test_hidden_type_is_not_shown_if_no_premission(self):
        self.assertNotIn(
            self.hidden_type_name,
            [
                i["name"]
                for i in getMultiAdapter(
                    (self.folder_prenotazioni, getRequest()), ISerializeToJson
                )()["booking_types"]
            ],
        )

    def test_not_hidden_type_is_being_shown(self):
        with api.env.adopt_roles(roles="Bookings Manager"):
            self.assertIn(
                self.not_hidden_type_name,
                [
                    i["name"]
                    for i in getMultiAdapter(
                        (self.folder_prenotazioni, getRequest()),
                        ISerializeToJson,
                    )()["booking_types"]
                ],
            )

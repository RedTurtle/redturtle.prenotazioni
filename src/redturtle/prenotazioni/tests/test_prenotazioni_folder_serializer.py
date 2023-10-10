# -*- coding: UTF-8 -*-
import email
import unittest
from datetime import date, datetime, timedelta

import pytz
from collective.contentrules.mailfromfield.actions.mail import (
    MailFromFieldAction,
)
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.contentrules.rule.interfaces import IExecutable
from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent
from zope.globalrequest import getRequest
from plone.restapi.interfaces import ISerializeToJson

from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING,
)


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestEmailToManagers(unittest.TestCase):
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
        week_table = self.folder_prenotazioni.week_table
        for data in week_table:
            data["morning_start"] = "0700"
            data["morning_end"] = "1000"
        self.folder_prenotazioni.week_table = week_table

    def test_hidden_type_is_not_shown(self):
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
        self.assertIn(
            self.not_hidden_type_name,
            [
                i["name"]
                for i in getMultiAdapter(
                    (self.folder_prenotazioni, getRequest()), ISerializeToJson
                )()["booking_types"]
            ],
        )

# -*- coding: UTF-8 -*-
import email
import unittest
from datetime import date, datetime, timedelta

import pytz
from collective.contentrules.mailfromfield.actions.mail import MailFromFieldAction
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.contentrules.rule.interfaces import IExecutable
from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

from redturtle.prenotazioni.adapters.booker import IBooker
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
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.folder_prenotazioni = api.content.create(
            container=self.portal,
            type="PrenotazioniFolder",
            title="Prenota foo",
            description="",
            daData=date.today(),
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
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

    def create_booking(self):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(
            {
                "booking_date": self.tomorrow_8_0,  # tomorrow
                "booking_type": "Type A",
                "title": "foo",
                "email": "jdoe@redturtle.it",
            }
        )

    def test_email_sent_to_managers_on_confirm(self):
        booking = self.create_booking()
        e = MailFromFieldAction()
        e.source = "foo@bar.be"
        e.fieldName = "email"
        e.target = "target"
        e.message = "Test mail"
        e.subject = "Subject"
        ex = getMultiAdapter(
            (
                self.portal,
                e,
                ActionSucceededEvent(
                    object=booking,
                    workflow=None,
                    action="confirm",
                    result="",
                ),
            ),
            IExecutable,
        )
        ex()

        mailSent = self.mailhost.messages[0]
        message = email.message_from_bytes(mailSent)

        # expected local time
        expected = self.tomorrow_8_0.strftime("%d/%m/%Y at 08:00")
        self.assertIn(expected, message.get_payload())

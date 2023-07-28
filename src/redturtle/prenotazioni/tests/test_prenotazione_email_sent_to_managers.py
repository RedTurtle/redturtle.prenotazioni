# -*- coding: UTF-8 -*-
from collective.contentrules.mailfromfield.actions.mail import MailFromFieldAction
from datetime import date, datetime
from datetime import timedelta
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.contentrules.rule.interfaces import IExecutable
from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent

import email
import unittest


@implementer(IObjectEvent)
class DummyEvent(object):
    def __init__(self, object):
        self.object = object


class TestSendIcal(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

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
            week_table=[
                {
                    "day": "Lunedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Martedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Mercoledì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Giovedì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Venerdì",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Sabato",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
                {
                    "day": "Domenica",
                    "morning_start": "0700",
                    "morning_end": "1000",
                    "afternoon_start": None,
                    "afternoon_end": None,
                },
            ],
            booking_types=[
                {"name": "Type A", "duration": "30"},
            ],
            gates=["Gate A"],
        )
        self.today = datetime.now().replace(hour=8)
        self.tomorrow = self.today + timedelta(1)
        self.folder_prenotazioni.email_responsabile = ["admin@test.com"]

    def create_booking(self):
        booker = IBooker(self.folder_prenotazioni)
        return booker.create(
            {
                "booking_date": self.tomorrow,  # tomorrow
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

        self.assertIn("admin@test.com", message.values())

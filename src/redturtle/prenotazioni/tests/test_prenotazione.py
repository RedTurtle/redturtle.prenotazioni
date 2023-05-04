# -*- coding: utf-8 -*-
from plone.autoform.interfaces import MODES_KEY
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from zope.interface import Interface

import unittest


class TestSchemaDirectives(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def test_field_modes(self):
        self.assertEqual(
            [
                (Interface, "booking_date", "display"),
                (Interface, "gate", "display"),
                (Interface, "booking_expiration_date", "display"),
            ],
            IPrenotazione.queryTaggedValue(MODES_KEY),
        )

# -*- coding: utf-8 -*-
import unittest

from redturtle.prenotazioni.content.prenotazioni_folder import holidays_constraint
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING


class TestPrenotazioniSearch(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
    maxDiff = None

    def setUp(self):
        self.postive_examples = ["12/12/2024", "31/01/*"]
        self.negative_examples = ["32/10/2024", "12/13/2025", "*/11/2023", "unparsed"]

    def test_holidays_constraint_positive(self):
        self.assertTrue(holidays_constraint(self.postive_examples))

    def test_holidays_constraint_negative(self):
        self.assertFalse(holidays_constraint(self.negative_examples))

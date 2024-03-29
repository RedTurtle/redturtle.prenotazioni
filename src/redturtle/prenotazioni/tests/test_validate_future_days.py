# -*- coding: utf-8 -*-
import unittest

from zope.interface import Invalid

from redturtle.prenotazioni.content.prenotazioni_folder import validate_future_days
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING


class Testf_futureDays_invariant(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def test_futureDays_requires_also_fiscalcode(self):
        class data_billet:
            futureDays = None
            required_booking_fields = None

        none_data = data_billet()
        none_data.futureDays = 0
        none_data.required_booking_fields = None

        self.assertIsNone(validate_future_days(none_data))

        negative_data = data_billet()
        negative_data.futureDays = 1
        negative_data.required_booking_fields = ["email"]

        self.assertRaises(Invalid, validate_future_days, negative_data)

        positive_data = data_billet()
        positive_data.futureDays = 1
        positive_data.required_booking_fields = ["email", "fiscalcode"]

        self.assertIsNone(validate_future_days(positive_data))

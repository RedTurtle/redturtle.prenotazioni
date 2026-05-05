# -*- coding: utf-8 -*-
import unittest

from zope.interface import Invalid

from redturtle.prenotazioni.content.prenotazioni_folder import (
    validate_max_bookings_allowed,
)
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING


class Testf_validate_max_bookings_allowed(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def test_validate_max_bookings_allowed(self):
        class data_billet:
            max_bookings_allowed = None
            required_booking_fields = None

        none_data = data_billet()
        none_data.max_bookings_allowed = 0
        none_data.required_booking_fields = None

        self.assertIsNone(validate_max_bookings_allowed(none_data))

        negative_data = data_billet()
        negative_data.max_bookings_allowed = 1
        negative_data.required_booking_fields = ["email"]

        self.assertRaises(Invalid, validate_max_bookings_allowed, negative_data)

        positive_data = data_billet()
        positive_data.max_bookings_allowed = 1
        positive_data.required_booking_fields = ["email", "fiscalcode"]

        self.assertIsNone(validate_max_bookings_allowed(positive_data))

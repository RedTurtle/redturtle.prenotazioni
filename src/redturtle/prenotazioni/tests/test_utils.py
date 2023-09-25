# -*- coding: utf-8 -*-
import unittest

import pytz

from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING


class TestUtils(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()

    def tearDown(self):
        pass

    def test_dateutils(self):
        self.assertEqual(
            datetime_with_tz("2023-08-09T13:30:00.000Z")
            .astimezone(pytz.utc)
            .isoformat(),
            "2023-08-09T13:30:00+00:00",
        )
        self.assertEqual(
            datetime_with_tz("2023-08-09T11:30:00.000+02")
            .astimezone(pytz.utc)
            .isoformat(),
            "2023-08-09T09:30:00+00:00",
        )

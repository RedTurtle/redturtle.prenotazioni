# -*- coding: utf-8 -*-
import unittest
from redturtle.prenotazioni.adapters.slot import BaseSlot
from datetime import datetime, timedelta
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING


class TestBaseSlot(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING
    maxDiff = None

    def test_sub(self):
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        a = [
            BaseSlot(now, now + timedelta(minutes=30)), 
            BaseSlot(now + timedelta(minutes=30), now + timedelta(hours=1)),
        ]
        b = BaseSlot(now, now + timedelta(hours=2))

        self.assertEqual(b - a, [BaseSlot(now + timedelta(hours=1), now + timedelta(hours=2))])

    def test_sub_overlapped(self):
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        a = [
            BaseSlot(now, now + timedelta(hours=1)), 
            BaseSlot(now + timedelta(minutes=30), now + timedelta(hours=1)),
        ]
        b = BaseSlot(now, now + timedelta(hours=2))

        self.assertEqual(b - a, [BaseSlot(now + timedelta(hours=1), now + timedelta(hours=2))])
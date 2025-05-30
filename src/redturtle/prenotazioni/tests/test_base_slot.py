# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING

import unittest


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

        self.assertEqual(
            b - a, [BaseSlot(now + timedelta(hours=1), now + timedelta(hours=2))]
        )

    def test_sub_with_holes(self):
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        a = [
            BaseSlot(now, now + timedelta(minutes=30)),
            BaseSlot(now + timedelta(minutes=75), now + timedelta(minutes=90)),
            BaseSlot(now + timedelta(minutes=105), now + timedelta(minutes=110)),
        ]
        b = BaseSlot(now + timedelta(minutes=60), now + timedelta(minutes=120))

        self.assertEqual(
            b - a,
            [
                BaseSlot(now + timedelta(minutes=60), now + timedelta(minutes=75)),
                BaseSlot(now + timedelta(minutes=90), now + timedelta(minutes=105)),
                BaseSlot(now + timedelta(minutes=110), now + timedelta(minutes=120)),
            ],
        )

    def test_sub_overlapped(self):
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        a = [
            BaseSlot(now, now + timedelta(hours=1)),
            BaseSlot(now + timedelta(minutes=30), now + timedelta(hours=1)),
        ]
        b = BaseSlot(now, now + timedelta(hours=2))

        self.assertEqual(
            b - a, [BaseSlot(now + timedelta(hours=1), now + timedelta(hours=2))]
        )

    def test_overlaps(self):
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        slot = BaseSlot(now, now + timedelta(hours=1))
        self.assertTrue(slot.overlaps(BaseSlot(now, now + timedelta(hours=1))))
        self.assertTrue(
            slot.overlaps(
                BaseSlot(now - timedelta(minutes=10), now + timedelta(minutes=10))
            )
        )
        self.assertTrue(
            slot.overlaps(
                BaseSlot(now + timedelta(minutes=10), now + timedelta(minutes=30))
            )
        )
        self.assertTrue(
            slot.overlaps(
                BaseSlot(now + timedelta(minutes=50), now + timedelta(minutes=70))
            )
        )

        self.assertFalse(
            slot.overlaps(
                BaseSlot(now - timedelta(minutes=20), now - timedelta(minutes=10))
            )
        )
        self.assertFalse(
            slot.overlaps(
                BaseSlot(now + timedelta(minutes=61), now - timedelta(minutes=70))
            )
        )

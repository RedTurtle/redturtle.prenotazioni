# -*- coding: utf-8 -*-
import unittest

from zope.interface import Invalid

from redturtle.prenotazioni.content.validators import validate_pause_table


class TestValidatePauseTable(unittest.TestCase):
    def setUp(self):
        self.week_table = [
            {
                "afternoon_end": "1900",
                "afternoon_start": "1230",
                "day": "Lunedì",
                "morning_end": "1100",
                "morning_start": "0700",
            },
            {
                "afternoon_end": None,
                "afternoon_start": None,
                "day": "Martedì",
                "morning_end": "1200",
                "morning_start": "0800",
            },
            {
                "afternoon_end": "1600",
                "afternoon_start": "1300",
                "day": "Mercoledì",
                "morning_end": None,
                "morning_start": None,
            },
            {
                "afternoon_end": None,
                "afternoon_start": None,
                "day": "Giovedì",
                "morning_end": None,
                "morning_start": None,
            },
            {
                "afternoon_end": None,
                "afternoon_start": None,
                "day": "Venerdì",
                "morning_end": None,
                "morning_start": None,
            },
            {
                "afternoon_end": None,
                "afternoon_start": None,
                "day": "Sabato",
                "morning_end": None,
                "morning_start": None,
            },
            {
                "afternoon_end": None,
                "afternoon_start": None,
                "day": "Domenica",
                "morning_end": None,
                "morning_start": None,
            },
        ]
        self.pause_table = [{"day": "0", "pause_start": "0730", "pause_end": "0800"}]
        self.data = type("Data", (), {"pause_table": None, "week_table": None})()
        self.data.pause_table = self.pause_table
        self.data.week_table = self.week_table

    def tearDown(self):
        del self.week_table
        del self.pause_table

    def test_validation_positive_morning(self):
        self.assertIsNone(validate_pause_table(data=self.data))

    def test_validation_positive_afternoon(self):
        self.data.pause_table.append(
            {"day": "0", "pause_start": "1300", "pause_end": "1400"}
        )
        self.assertIsNone(validate_pause_table(data=self.data))

    def test_negative_interval_not_in_slot(self):
        self.pause_table[0]["pause_end"] = "1130"

        self.assertRaises(Invalid, validate_pause_table, data=self.data)

    def test_negative_pause_overlap(self):
        self.pause_table.append(
            {"day": "0", "pause_start": "0725", "pause_end": "8000"}
        )

        self.assertRaises(Invalid, validate_pause_table, data=self.data)

    def test_negative_end_lower_than_start(self):
        self.pause_table[0]["pause_end"] = "0725"

        self.assertRaises(Invalid, validate_pause_table, data=self.data)

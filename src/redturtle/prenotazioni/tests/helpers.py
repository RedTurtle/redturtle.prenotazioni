# -*- coding: utf-8 -*-
WEEK_TABLE_SCHEMA = [
    {
        "day": "Lunedì",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Martedì",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Mercoledì",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Giovedì",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Venerdì",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Sabato",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
    {
        "day": "Domenica",
        "morning_start": "0700",
        "morning_end": "1300",
        "afternoon_start": None,
        "afternoon_end": None,
    },
]


PRENOTAZIONE_TYPE_TIME_RANGE_BEHAVIOR = "prenotazione_type_time_range"


def enable_prenotazione_type_time_range_behavior(portal):
    fti = portal.portal_types["PrenotazioneType"]
    behaviors = tuple(fti.behaviors or ())
    if PRENOTAZIONE_TYPE_TIME_RANGE_BEHAVIOR in behaviors:
        return
    fti.behaviors = behaviors + (PRENOTAZIONE_TYPE_TIME_RANGE_BEHAVIOR,)

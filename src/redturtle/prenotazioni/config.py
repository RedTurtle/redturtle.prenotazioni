# -*- coding: utf-8 -*-

PROJECTNAME = "redturtle.prenotazioni"

MIN_IN_DAY = 24 * 60
PAUSE_SLOT = "pause_slot"
PAUSE_PORTAL_TYPE = "DayPause"
VERIFIED_BOOKING = "redturtle.prenotazioni.verified_booking"
NOTIFICATIONS_LOGS = "redturtle.prenotazioni.notifications_logs"
REQUIRABLE_AND_VISIBLE_FIELDS = [
    "email",
    "phone",
    "fiscalcode",
    "company",
    "description",
]
DEFAULT_VISIBLE_BOOKING_FIELDS = ["email", "phone", "description"]
STATIC_REQUIRED_FIELDS = ["title"]

# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from redturtle.prenotazioni import tznow
from plone.app.event.base import default_timezone
import pytz


def exceedes_date_limit(data, future_days):
    """
    Check if the booking date exceedes the date limit
    """
    if not future_days:
        return False
    booking_date = data.get("booking_date", None)
    if not isinstance(booking_date, datetime):
        return False
    date_limit = tznow() + timedelta(future_days)
    if not booking_date.tzinfo:
        tzinfo = date_limit.tzinfo
        if tzinfo:
            booking_date = tzinfo.localize(booking_date)
    if booking_date <= date_limit:
        return False
    return True


def as_naive_utc(dt):
    tz = default_timezone(as_tzinfo=True)
    return tz.localize(dt).astimezone(pytz.utc).replace(tzinfo=None)

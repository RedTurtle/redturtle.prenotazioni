# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import time
from datetime import timedelta

import six
from plone.app.event.base import default_timezone

from redturtle.prenotazioni import tznow


def hm2handm(hm):
    """This is a utility function that will return the hour and date of day
    to the value passed in the string hm

    :param hm: a string in the format "%H%m"

    XXX: manage the case of `hm` as tuple, eg. ("0700", )
    """
    if hm and isinstance(hm, tuple):
        hm = hm[0]
    if (not hm) or (not isinstance(hm, six.string_types)) or (len(hm) != 4):
        raise ValueError(hm)
    return (hm[:2], hm[2:])


def hm2DT(day, hm, tzinfo=None):
    """This is a utility function that will return the hour and date of day
    to the value passed in the string hm

    :param day: a datetime date
    :param hm: a string in the format "%H%m" or "%H:%m"
    :param tzinfo: a timezone object (default: the default local timezone as in plone)
    """
    if tzinfo is None:
        tzinfo = default_timezone(as_tzinfo=True)

    if not hm or hm == "--NOVALUE--" or hm == ("--NOVALUE--",):
        return None
    if len(hm) == 4 and ":" not in hm:
        hm = f"{hm[:2]}:{hm[2:]}"
    return tzinfo.localize(datetime.combine(day, time.fromisoformat(hm)))


def hm2seconds(hm):
    """This is a utility function that will return
    to the value passed in the string hm

    :param hm: a string in the format "%H%m"
    """
    if not hm:
        return None
    h, m = hm2handm(hm)
    return int(h) * 3600 + int(m) * 60


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

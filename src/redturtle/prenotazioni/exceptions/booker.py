# -*- coding: utf-8 -*-
from plone import api

from redturtle.prenotazioni import _


class BookerException(Exception):
    pass


class BookingsLimitExceded(BookerException):
    def __init__(self, bookings_folder=None, *args, **kwargs):
        return super().__init__(
            api.portal.translate(
                _(
                    "bookings_limit_exceeded_exception",
                    default="Booking limit({limit}) is exceed for the current user",
                )
            ).format(limit=bookings_folder.max_bookings_allowed),
            *args,
            **kwargs
        )

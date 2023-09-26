# -*- coding: utf-8 -*-
class BookerException(Exception):
    pass


class BookingsLimitExceded(BookerException):
    def __init__(self, *args, **kwargs):
        if "message" not in kwargs.keys():
            kwargs["message"] = "Booking limit is exceed for the current user"

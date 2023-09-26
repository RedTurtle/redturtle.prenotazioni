# -*- coding: utf-8 -*-
class BookerException(Exception):
    pass


class BookingsLimitExceded(BookerException):
    def __init__(
        self, message="Booking limit is exceed for the current user", *args, **kwargs
    ):
        return super().__init__(message, *args, **kwargs)

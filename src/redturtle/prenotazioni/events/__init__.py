# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent

from redturtle.prenotazioni.interfaces import IBookingReminderEvent


@implementer(IBookingReminderEvent)
class BookingReminderEvent(ObjectEvent):
    def __init__(self, obj):
        super().__init__(obj)

# -*- coding: utf-8 -*-
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent


@implementer(IBookingReminderEvent)
class BookingReminderEvent(ObjectEvent):
    pass

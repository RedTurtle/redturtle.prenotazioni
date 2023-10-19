# -*- coding: utf-8 -*-
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.booking_type import IBookingType
from redturtle.prenotazioni.interfaces import (
    IRedturtlePrenotazioniLayer,
    ISerializeToRetrocompattibleJson,
)


@implementer(ISerializeToRetrocompattibleJson)
@adapter(IBookingType, IRedturtlePrenotazioniLayer)
class BookingTypeRetrocompattibleSerializer:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, *args, **kwargs):
        return {
            "name": self.context.title,
            "duration": str(self.context.duration),
        }

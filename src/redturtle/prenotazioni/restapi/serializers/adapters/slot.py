# -*- coding: utf-8 -*-
from datetime import time, datetime
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import json_compatible
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni.adapters.slot import ISlot
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces import IRequest


@implementer(ISerializeToJson)
@adapter(ISlot, IRequest)
class SlotSerializer:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def hr_to_utc(self, value):
        """
        Attributes:
            value (str): "%H:%M" formatted string

        Returns:
            str: An iso formatted datetime string with timezone
        """
        if not value:
            return None
        value = value.split(":")

        time_ = time(
            hour=int(value[0]),
            minute=int(value[1]),
        )
        date = getattr(self.context, "date")

        if not date:
            return time_.isoformat()
        return json_compatible(datetime_with_tz(datetime.combine(date, time_)))

    def __call__(self, *args, **kwargs):
        return {
            "start": self.hr_to_utc(self.context.start()),
            "end": self.hr_to_utc(self.context.stop()),
        }

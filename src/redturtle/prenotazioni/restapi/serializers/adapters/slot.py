# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plone.app.event.base import default_timezone
from redturtle.prenotazioni.adapters.slot import ISlot
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces import IRequest
from datetime import time, datetime

import pytz


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

        return (
            pytz.timezone(default_timezone())
            .localize(datetime.combine(date, time_))
            .astimezone(pytz.timezone("UTC"))
        ).isoformat()

    def __call__(self, *args, **kwargs):
        return {
            "start": self.hr_to_utc(self.context.start()),
            "stop": self.hr_to_utc(self.context.stop()),
        }

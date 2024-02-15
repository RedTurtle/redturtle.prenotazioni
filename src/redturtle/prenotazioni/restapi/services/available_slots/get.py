# -*- coding: utf-8 -*-
import calendar
import datetime
from datetime import timedelta

from plone import api
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zExceptions import BadRequest

from redturtle.prenotazioni import _


class AvailableSlots(Service):
    def reply(self):
        """
        Finds all the available slots in a month.

        If you pass a start and end date, the search will be made between these dates.

        If not, the search will start from current date until the end of current month.
        """
        # XXX: nocache also for anonymous
        self.request.response.setHeader("Cache-Control", "no-cache")

        prenotazioni_context_state = api.content.get_view(
            "prenotazioni_context_state",
            self.context,
            self.request,
        )

        start = self.request.form.get("start", "")
        end = self.request.form.get("end", "")
        past_slots = self.request.form.get("past_slots", False)

        if start:
            start = datetime.date.fromisoformat(start)
        else:
            start = datetime.date.today()

        if end:
            end = datetime.date.fromisoformat(end)
        else:
            end = start.replace(day=calendar.monthrange(start.year, start.month)[1])

        if start > end:
            msg = self.context.translate(
                _(
                    "available_slots_wrong_dates",
                    default="End date should be greater than start.",
                )
            )
            raise BadRequest(msg)

        booking_type = self.request.form.get("booking_type")
        if booking_type:
            slot_min_size = (
                prenotazioni_context_state.get_booking_type_duration(booking_type) * 60
            )
        else:
            slot_min_size = 0

        response = {
            "@id": f"{self.context.absolute_url()}/@available-slots",
            "items": [],
        }
        for n in range(int((end - start).days) + 1):
            booking_date = start + timedelta(n)
            slots = prenotazioni_context_state.get_anonymous_slots(
                booking_date=booking_date
            )
            for slot in slots.get("anonymous_gate", []):
                info = prenotazioni_context_state.get_anonymous_booking_url(
                    booking_date, slot, slot_min_size=slot_min_size
                )
                if not info.get("url", ""):
                    continue
                if not past_slots and not info.get("future"):
                    continue
                response["items"].append(json_compatible(info.get("booking_date", "")))
        return response


# from mrs.doubtfire.meta import metricmethod
# AvailableSlots.reply = metricmethod(AvailableSlots.reply)

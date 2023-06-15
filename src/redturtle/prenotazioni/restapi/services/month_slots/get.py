# -*- coding: utf-8 -*-
from datetime import date
from plone import api
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service

import calendar


class MonthSlots(Service):
    def reply(self):
        """
        Finds all the available slots in a month.

        If you pass a date in querystring, the search will start from that date during the whole month.
        If not, the search will start from current date.
        """

        prenotazioni_week_view = api.content.get_view(
            "prenotazioni_week_view", context=self.context, request=self.request
        )
        now = self.request.form.get("date", "")
        if now:
            now = date.fromisoformat(now)
        else:
            now = date.today()
        booking_type = self.request.form.get("booking_type")
        if booking_type:
            slot_min_size = (
                prenotazioni_week_view.prenotazioni.get_booking_type_duration(
                    booking_type
                )
                * 60
            )  # noqa
        else:
            slot_min_size = 0
        start_year = now.year
        start_month = now.month
        start_day = now.day

        response = {"@id": f"{self.context.absolute_url()}/@month_slots", "items": []}
        for week in calendar.monthcalendar(start_year, start_month):
            for day in week:
                if day < start_day:
                    continue
                booking_date = date(start_year, start_month, day)
                slots = prenotazioni_week_view.prenotazioni.get_anonymous_slots(
                    booking_date=booking_date
                )
                for slot in slots.get("anonymous_gate", []):
                    info = (
                        prenotazioni_week_view.prenotazioni.get_anonymous_booking_url(
                            booking_date, slot, slot_min_size=slot_min_size
                        )
                    )
                    if not info.get("url", ""):
                        continue
                    response["items"].append(
                        json_compatible(info.get("booking_date", ""))
                    )
        return response

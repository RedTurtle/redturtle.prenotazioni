# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from zExceptions import BadRequest

from redturtle.prenotazioni.adapters.slot import ISlot

from datetime import datetime, date


class WeekSlots(Service):
    def reply(self):
        """
        Finds all the available and busy slots in a week which is taken in base of
        `data` param passed by the request or the current one.

        Returns:
            dict: contains all the busy slots of the day. Dict format:
                    `{
                        "@id": "http://localhost:8080/Plone/prenotazioni_folder/@day_busy_slots",
                        "bookings": {
                            "gate1": [
                                {
                                    "booking_id": "e43d8d8b83bd48e08ff94d732740b090",
                                    "start": "09:20",
                                    "stop": "10:20"
                                },
                                {
                                    "booking_id": "994b2dad8d8a4f389e1fdc9afdded489",
                                    "start": "11:50",
                                    "stop": "12:50"
                                },
                                {
                                    "booking_id": "1599103b30b648c099005074693fe27c",
                                    "start": "15:50",
                                    "stop": "16:50"
                                }
                            ]
                        },
                        "pauses": [
                            {
                                "start": "07:15",
                                "stop": "08:30"
                            }
                        ]
                    }`
        """

        day_date = self.request.form.get("date")

        if day_date:
            try:
                day_date = datetime.strptime(day_date, "%d/%m/%Y").date()
            except ValueError as e:
                raise BadRequest(str(e))

        else:
            day_date = date.today()

        prenotazioni_context_state_view = api.content.get_view(
            "prenotazioni_context_state",
            context=self.context,
            request=self.request,
        )

        bookings = prenotazioni_context_state_view.get_bookings_in_day_folder(
            day_date
        )

        bookings_result = {}

        for gate in {i.gate for i in bookings}:
            bookings_result[gate] = [
                {
                    **getMultiAdapter((i, self.request), ISerializeToJson)(),
                }
                for i in bookings
                if i.gate == gate
            ]

        pauses_serialized = [
            getMultiAdapter((ISlot(i), self.request), ISerializeToJson)()
            for i in prenotazioni_context_state_view.get_pauses_in_day_folder(
                day_date
            )
        ]

        return {
            "@id": f"{self.context.absolute_url()}/@day-busy-slots",
            "bookings": bookings_result,
            "pauses": pauses_serialized,
        }

# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from zExceptions import BadRequest

from redturtle.prenotazioni.adapters.slot import ISlot

from datetime import datetime, date


class WeekSlots(Service):
    def __init__(self, context, request):
        super().__init__(context=context, request=request)
        self.prenotazioni_context_state = api.content.get_view(
            "prenotazioni_context_state",
            context=self.context,
            request=self.request,
        )

        day_date = self.request.form.get("date")

        if day_date:
            try:
                day_date = datetime.strptime(day_date, "%d/%m/%Y").date()
            except ValueError as e:
                raise BadRequest(str(e))

        else:
            day_date = date.today()

        self.day_date = day_date

    def reply(self):
        """
        Finds all the busy slots in a week which is taken in base of
        `data` param passed by the request or the current one.

        Returns:
            dict: contains all the busy slots of the day. Dict format:
                    `{
                        "@id": "http://localhost:8080/Plone/prenotazioni_folder/@day_busy_slots",
                        "bookings": {
                            "gate1":
                                [
                                    {
                                        "booking_code": "17E3E6",
                                        "booking_date": "2023-05-22T09:09:00",
                                        "booking_expiration_date": "2023-05-22T09:10:00+00:00",
                                        "booking_type": "xxx",
                                        "company": null,
                                        "cosa_serve": null,
                                        "description": "",
                                        "email": "mario.rossi@example",
                                        "fiscalcode": "",
                                        "gate": "postazione1",
                                        "id": "mario-rossi-1",
                                        "phone": "",
                                        "staff_notes": null,
                                        "title": "Mario Rossi"
                                    },
                                    ...
                                ],
                            "gate2":
                                [
                                    {
                                        "booking_code": "17E3E6",
                                        "booking_date": "2023-05-22T09:09:00+00:00",
                                        "booking_expiration_date": "2023-05-22T09:10:00+00:00",
                                        "booking_type": "yyy",
                                        "company": null,
                                        "cosa_serve": null,
                                        "description": "",
                                        "email": "mario.rossi@example",
                                        "fiscalcode": "",
                                        "gate": "postazione2",
                                        "id": "mario-rossi",
                                        "phone": "",
                                        "staff_notes": null,
                                        "title": "Mario Rossi"
                                    },
                                    ...
                                ]
                        },
                        "pauses": [
                            {
                                "start": "2023-05-22T07:15:00+00:00",
                                "stop": "2023-05-22T08:30:00+00:00"
                            },
                            ...
                        ]
                        "daily_schedule": {
                            "afternoon": {
                                "start": "2023-05-22T12:00:00+00:00",
                                "stop": "2023-05-22T16:00:00+00:00"
                            },
                            "morning": {
                                "start": "2023-05-22T05:00:00+00:00",
                                "stop": "2023-05-22T11:00:00+00:00"
                            }
                        }
                    }`
        """

        return {
            "@id": f"{self.context.absolute_url()}/@day-busy-slots",
            "bookings": self.get_bookings(),
            "pauses": self.get_pauses(),
            "daily_schedule": self.get_daily_schedule(),
        }

    def get_bookings(self):

        bookings = self.prenotazioni_context_state.get_bookings_in_day_folder(
            self.day_date
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
        return bookings_result

    def get_pauses(self):
        return [
            getMultiAdapter((ISlot(i), self.request), ISerializeToJson)()
            for i in self.prenotazioni_context_state.get_pauses_in_day_folder(
                self.day_date
            )
        ]

    def get_daily_schedule(self):
        intervals = self.prenotazioni_context_state.get_day_intervals(self.day_date)

        if not intervals:
            return {}
        return {
            "morning": getMultiAdapter(
                (intervals["morning"], self.request), ISerializeToJson
            )(),
            "afternoon": getMultiAdapter(
                (intervals["afternoon"], self.request), ISerializeToJson
            )(),
        }

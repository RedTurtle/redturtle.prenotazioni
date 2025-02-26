# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from plone import api
from plone.memoize.view import memoize
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from redturtle.prenotazioni.adapters.slot import ISlot
from zExceptions import BadRequest
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class DaySlots(Service):
    day = None

    def publishTraverse(self, request, day):
        if self.day is None:
            try:
                self.day = datetime.fromisoformat(day).date()
            except ValueError:
                raise BadRequest("Invalid date")
        return self

    @property
    @memoize
    def prenotazioni_context_state(self):
        return api.content.get_view(
            "prenotazioni_context_state",
            context=self.context,
            request=self.request,
        )

    def reply(self):
        """
        Finds all the busy slots in a week which is taken in base of
        `data` param passed by the request or the current one.

        Returns:
            dict: contains all the busy slots of the day. Dict format:
                    `{
                        "@id": "http://localhost:8080/Plone/prenotazioni_folder/@day/2023-05-22",
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

        if self.day is None:
            self.day = date.today()

        response = {
            "@id": f"{self.context.absolute_url()}/@day/{self.day.isoformat()}",
        }

        # check if date is in the Booking Folder availability dates range
        if self.context.daData <= self.day and (
            not self.context.aData or self.context.aData >= self.day
        ):
            response.update(
                {
                    "bookings": self.get_bookings(),
                    "pauses": self.get_pauses(),
                    "gates": self.get_gates(),
                }
            )
        else:
            response.update(
                {
                    "bookings": [],
                    "pauses": [],
                    "gates": [],
                }
            )

        return response

    def get_bookings(self):
        bookings = self.prenotazioni_context_state.get_bookings_in_day_folder(self.day)
        bookings_result = {}
        for gate in {i.gate for i in bookings}:
            bookings_result[gate] = [
                getMultiAdapter((booking, self.request), ISerializeToJson)()
                for booking in bookings
                if booking.gate == gate
            ]
        return bookings_result

    def get_pauses(self):
        return [
            getMultiAdapter((ISlot(i), self.request), ISerializeToJson)()
            for i in self.prenotazioni_context_state.get_pauses_in_day_folder(self.day)
        ]

    def get_gates(self):
        gates = self.prenotazioni_context_state.get_gates(self.day)
        intervals = self.prenotazioni_context_state.get_day_intervals(self.day)
        for gate in gates:
            gate["daily_schedule"] = {}
            for period in ["morning", "afternoon"]:
                interval = intervals.get(period, {})["gates"].get(gate["name"], None)
                if interval:
                    gate["daily_schedule"][period] = getMultiAdapter(
                        (interval, self.request), ISerializeToJson
                    )()
                else:
                    gate["daily_schedule"][period] = {"start": None, "end": None}
        return gates

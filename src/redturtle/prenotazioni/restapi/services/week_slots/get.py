# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter


class WeekSlots(Service):
    def reply(self):
        """
        Finds all the available and busy slots in a week which is taken in base of
        `data` param passed by the request or the current one.

        Returns:
            dict: contains all the free and busy slots of the week. Dict format:
                    `{
                        '01-01-1970':
                            {
                                'busy_slots': [
                                    'Gate': {
                                        'start': '09:00',
                                        'stop': '09:30'
                                    ],
                                    'Gate1': [],
                                    ...
                                },
                                'free_slots': {
                                    'Gate': [
                                        'start': '09:30',
                                        'stop': '12:00'
                                    ],
                                    'Gate1': [
                                        'start': '09:00',
                                        'stop': '12:00'
                                    ],
                                    ...
                                }
                            },
                            ...
                        }`
        """

        prenotazioni_week_view = api.content.get_view(
            "prenotazioni_week_view", context=self.context, request=self.request
        )
        prenotazioni_context_state_view = api.content.get_view(
            "prenotazioni_context_state", context=self.context, request=self.request
        )
        response = {}

        for week_day in prenotazioni_week_view.actual_week_days:
            free_slots = prenotazioni_context_state_view.get_free_slots(week_day)
            busy_slots = prenotazioni_context_state_view.get_busy_slots(week_day)
            week_day_key = week_day.isoformat()

            # build the response
            response[week_day_key] = {}
            response[week_day_key]["busy_slots"] = {}
            response[week_day_key]["free_slots"] = {}

            for name, value in free_slots.items():
                response[week_day_key]["free_slots"][name] = [
                    getMultiAdapter((item, self.request), ISerializeToJson)()
                    for item in value
                ]

            for name, value in busy_slots.items():
                response[week_day_key]["busy_slots"][name] = [
                    getMultiAdapter((item, self.request), ISerializeToJson)()
                    for item in value
                ]

        return response

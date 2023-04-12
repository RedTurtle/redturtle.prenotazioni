# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.services import Service
from DateTime import DateTime
import time


class BookingSchema(Service):
    def reply(self):
        """
        Return the schema for the booking form.

        """

        booking_context_state_view = api.content.get_view(
            "prenotazioni_context_state", context=self.context, request=self.request
        )

        current_user = None
        response = {}

        booking_folder = self.context
        if not api.user.is_anonymous():
            current_user = api.user.get_current()

        booking_date = self.request.form.get("form.booking_date", None)

        if not booking_date:
            raise ValueError("Wrong date format")

        tzname = time.tzname[time.daylight]

        if len(booking_date) != 16:
            raise ValueError("Wrong date format")

        if tzname == "RMT":
            tzname = "CEST"
        booking_date = " ".join((booking_date, tzname))

        try:
            booking_date = DateTime(booking_date).asdatetime()
        except ValueError:
            raise ValueError("Wrong date format")

        bookings = booking_context_state_view.booking_types_bookability(booking_date)

        fields_list = []
        for field in booking_folder.visible_booking_fields:
            value = ""
            is_mandatory = False
            is_readonly = False

            if field in booking_folder.required_booking_fields:
                is_mandatory = True

            if current_user:
                is_readonly = True

                if field == "email":
                    value = current_user.getProperty("email")
                if field == "fiscalcode":
                    value = current_user.getUserName()

            fields_list.append(
                {
                    "name": field,
                    "value": value,
                    "required": is_mandatory,
                    "readonly": is_readonly,
                }
            )
        if current_user:
            user_name = current_user.getProperty("fullname")
            fields_list.append(
                {
                    "name": "title",
                    "value": user_name,
                    "required": True,
                    "readonly": True,
                }
            )

        res = {"bookable": [], "unbookable": []}
        for item in booking_folder.booking_types:
            if item["name"] in bookings["bookable"]:
                res["bookable"].append(item)
            else:
                res["unbookable"].append(item)

        response.update({"fields": fields_list})
        response.update({"booking_types": res})

        return response

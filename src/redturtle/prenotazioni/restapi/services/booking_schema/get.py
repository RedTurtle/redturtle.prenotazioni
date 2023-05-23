# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.services import Service

import time

desc_map = {
    "email": {
        "label": "Email",
        "description": "Inserisci l'email",
    },
    "fiscalcode": {
        "label": "Codice Fiscale",
        "description": "Inserisci il codice fiscale",
    },
    "phone": {
        "label": "Numero di telefono",
        "description": "Inserisci il numero di telefono",
    },
    "description": {
        "label": "Note",
        "description": "Inserisci ulteriori informazioni",
    },
    "company": {
        "label": "Azienda",
        "description": "Inserisci il nome dell'azienda",
    },
}


class BookingSchema(Service):
    def reply(self):  # noqa: C901
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

        booking_date = booking_date.replace("T", " ")

        tzname = time.tzname[time.daylight]

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
            label = ""
            desc = ""
            is_mandatory = False
            is_readonly = False
            field_type = "text"

            if field == "description":
                field_type = "textarea"

            if (
                booking_folder.required_booking_fields
                and field in booking_folder.required_booking_fields
            ):
                is_mandatory = True

            if current_user:
                if field == "email":
                    value = current_user.getProperty("email")
                    is_readonly = True

                if field == "fiscalcode":
                    value = current_user.getUserName()
                    is_readonly = True

            if field in desc_map.keys():
                label = desc_map.get(field).get("label")
                desc = desc_map.get(field).get("description")

            fields_list.append(
                {
                    "label": label,
                    "desc": desc,
                    "type": field_type,
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
                    "label": "Nome completo",
                    "desc": "Inserire il nome completo",
                    "type": "text",
                    "name": "Nome",
                    "value": user_name,
                    "required": True,
                    "readonly": True,
                }
            )
        else:
            fields_list.append(
                {
                    "label": "Nome completo",
                    "desc": "Inserire il nome completo",
                    "type": "text",
                    "name": "Nome",
                    "value": "",
                    "required": True,
                    "readonly": False,
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
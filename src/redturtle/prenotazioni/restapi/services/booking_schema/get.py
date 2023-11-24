# -*- coding: utf-8 -*-
from plone import api
from plone.memoize.view import memoize
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.component import getMultiAdapter

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni.config import STATIC_REQUIRED_FIELDS
from redturtle.prenotazioni.interfaces import ISerializeToRetroCompatibleJson


class BookingSchema(Service):
    field_type_mapping = {"description": "textarea"}

    # TODO: rendere traudcibili label e descrizione
    labels_mapping = {
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
            "description": "Aggiungi ulteriori dettagli",
        },
        "company": {
            "label": "Azienda",
            "description": "Inserisci il nome dell'azienda",
        },
        "title": {
            "label": "Nome completo",
            "description": "Inserire il nome completo",
        },
    }

    @property
    @memoize
    def required_fields(self):
        required_booking_fields = (
            getattr(
                self.context,
                "required_booking_fields",
                [],
            )
            or []
        )
        fields = [x for x in required_booking_fields]
        for field in STATIC_REQUIRED_FIELDS:
            if field not in fields:
                fields.append(field)
        return fields

    def reply(self):
        """
        Return the schema for the booking form.

        """

        # validation
        if not self.request.form.get("booking_date", None):
            msg = api.portal.translate(
                _(
                    "schema_missing_date",
                    default="You need to provide a booking date to get the schema and available types.",
                )
            )
            raise BadRequest(msg)

        current_user = None

        if not api.user.is_anonymous():
            current_user = api.user.get_current()

        fields_list = []
        fields = [x for x in STATIC_REQUIRED_FIELDS]
        fields += [
            x
            for x in self.context.visible_booking_fields
            if x not in STATIC_REQUIRED_FIELDS
        ]
        for field in fields:
            value = ""
            is_readonly = False

            if current_user:
                if field == "email":
                    value = current_user.getProperty("email")
                    # readonly solo se ha un valore
                    is_readonly = bool(value)
                if field == "fiscalcode":
                    value = current_user.getUserName()
                    is_readonly = True
                if field == "title":
                    value = current_user.getProperty("fullname")
                    # readonly solo se ha un valore
                    is_readonly = bool(value)

            fields_list.append(
                {
                    "label": self.labels_mapping.get(field, {}).get("label", field),
                    "desc": self.labels_mapping.get(field, {}).get("description", ""),
                    "type": self.field_type_mapping.get(field, "text"),
                    "name": field,
                    "value": value,
                    "required": field in self.required_fields,
                    "readonly": is_readonly,
                }
            )

        return {
            "fields": fields_list,
            "booking_types": self.get_booking_types(),
        }

    def get_booking_types(self):
        booking_date = self.request.form.get("booking_date", None)
        res = {"bookable": [], "unbookable": []}

        if not booking_date:
            return res

        booking_context_state_view = api.content.get_view(
            "prenotazioni_context_state",
            context=self.context,
            request=self.request,
        )

        # fix timezone notation. querystring replaced + with a space
        booking_date = booking_date.replace(" 00:00", "+00:00")
        booking_date = datetime_with_tz(booking_date)

        bookings = booking_context_state_view.booking_types_bookability(booking_date)

        for item in self.context.get_booking_types():
            serialized_item = getMultiAdapter(
                (item, self.request), ISerializeToRetroCompatibleJson
            )()

            if item.title in bookings["bookable"]:
                res["bookable"].append(serialized_item)
            else:
                res["unbookable"].append(serialized_item)

        return res

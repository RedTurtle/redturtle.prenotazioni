# -*- coding: utf-8 -*-
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import ISerializeToJson
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.restapi.services.booking_schema.get import BookingSchema
from zExceptions import BadRequest
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides


# src/redturtle/prenotazioni/browser/prenotazione_add.py


class AddBooking(BookingSchema):
    """
    Add a new booking
    """

    def reply(self):
        data = json_body(self.request)
        data_fields = {field["name"]: field["value"] for field in data["fields"]}

        self.validate()

        alsoProvides(self.request, IDisableCSRFProtection)

        booker = IBooker(self.context.aq_inner)

        book_data = {
            "booking_date": data["booking_date"],
            "booking_type": data["booking_type"],
        }
        for field in data_fields:
            book_data[field] = data_fields[field]

        obj = booker.book(data=book_data)

        if not obj:
            msg = self.context.translate(
                _("Sorry, this slot is not available anymore.")
            )
            raise BadRequest(msg)

        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        return serializer()

    def validate(self):
        data = json_body(self.request)
        data_fields = {field["name"]: field["value"] for field in data["fields"]}

        missing_str = "Required input '${field}' is missing."

        # campi che non sono nei data_fields
        for field in ("booking_date", "booking_type"):
            if not data.get(field):
                msg = self.context.translate(
                    _(
                        missing_str,
                        mapping=dict(field=field),
                    )
                )
                raise BadRequest(msg)
        for field in self.required_fields:
            if not data_fields.get(field):
                msg = self.context.translate(
                    _(
                        missing_str,
                        mapping=dict(field=field),
                    )
                )
                raise BadRequest(msg)

        if data["booking_type"] not in [
            _t["name"] for _t in self.context.booking_types or [] if "name" in _t
        ]:
            msg = self.context.translate(
                _(
                    "Unknown booking type '${booking_type}'.",
                    mapping=dict(booking_type=data["booking_type"]),
                )
            )
            raise BadRequest(msg)

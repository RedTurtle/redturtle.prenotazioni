# -*- coding: utf-8 -*-
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import IBooker
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zExceptions import BadRequest

# src/redturtle/prenotazioni/browser/prenotazione_add.py


class AddBooking(Service):
    """
    Add a new booking
    """

    def reply(self):
        data = json_body(self.request)
        data_fields = {field["name"]: field["value"] for field in data["fields"]}

        required = self.context.required_booking_fields or []

        # la tipologia di una prenotazione deve essere sempre obbligatoria ticket: 19131
        for field in ("booking_date", "booking_type"):
            if not data.get(field):
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
                        mapping=dict(field=field),
                    )
                )
                raise BadRequest(msg)

        for field in required:
            if field in ("booking_date", "booking_type"):
                continue
            if not data_fields.get(field):
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
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

# -*- coding: utf-8 -*-
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import ISerializeToJson
from zExceptions import BadRequest
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides

from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.content.prenotazione import VACATION_TYPE
from redturtle.prenotazioni.restapi.services.booking_schema.get import BookingSchema

# src/redturtle/prenotazioni/browser/prenotazione_add.py


class AddBooking(BookingSchema):
    """
    Add a new booking
    """

    def reply(self):
        data, data_fields = self.validate()
        force = data.get("force", False)
        booker = IBooker(self.context.aq_inner)
        book_data = {
            "booking_date": data["booking_date"],
            "booking_type": data["booking_type"],
        }
        for field in data_fields:
            book_data[field] = data_fields[field]
        alsoProvides(self.request, IDisableCSRFProtection)
        try:
            if force:
                # TODO: in futuro potrebbe forzare anche la data di fine oltre al gate
                # create ha un parametro "duration" che può essere usato a questo scopo

                if not api.user.has_permission(
                    "redturtle.prenotazioni: Manage Prenotazioni",
                    obj=self.context,
                ):
                    msg = self.context.translate(
                        _("You are not allowed to force the gate.")
                    )
                    raise BadRequest(msg)
                gate = data.get("gate", None)
                duration = int(data.get("duration", -1))
                obj = booker.book(data=book_data, force_gate=gate, duration=duration)
            else:
                obj = booker.book(data=book_data)
        except BookerException as e:
            raise BadRequest(str(e))
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

        # campi che non sono nei data_fields
        for field in ("booking_date", "booking_type"):
            if not data.get(field):
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
                        mapping=dict(field=field),
                    )
                )
                raise BadRequest(msg)

        if data["booking_type"] in [VACATION_TYPE]:
            if not api.user.has_permission(
                "redturtle.prenotazioni: Manage Prenotazioni", obj=self.context
            ):
                msg = self.context.translate(
                    _(
                        "unauthorized_add_vacation",
                        "You can't add a booking with type '${booking_type}'.",
                        mapping=dict(booking_type=data["booking_type"]),
                    )
                )
                raise BadRequest(msg)
            # TODO: check permission for special booking_types ?
            return data, data_fields

        for field in self.required_fields:
            if not data_fields.get(field):
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
                        mapping=dict(field=field),
                    )
                )
                raise BadRequest(msg)

        if data["booking_type"] not in [
            _t.title for _t in self.context.get_booking_types()
        ]:
            msg = self.context.translate(
                _(
                    "Unknown booking type '${booking_type}'.",
                    mapping=dict(booking_type=data["booking_type"]),
                )
            )
            raise BadRequest(msg)

        return data, data_fields

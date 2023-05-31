# -*- coding: utf-8 -*-
from datetime import datetime
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.utilities.dateutils import exceedes_date_limit
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides


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
                self.request.response.setStatus(400)
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
                        mapping=dict(field=field),
                    )
                )
                return dict(error=dict(type="Bad Request", message=msg))

        if isinstance(data["booking_date"], str):
            # TODO: redturtle.prenotazioni lavora con date naive, quindi toglia la timezone
            #       ma non dovrebbe essere così
            data["booking_date"] = datetime.fromisoformat(data["booking_date"]).replace(
                tzinfo=None
            )

        for field in required:
            if field in ("booking_date", "booking_type"):
                continue
            if not data_fields.get(field):
                self.request.response.setStatus(400)
                msg = self.context.translate(
                    _(
                        "Required input '${field}' is missing.",
                        mapping=dict(field=field),
                    )
                )
                return dict(error=dict(type="Bad Request", message=msg))

        if data["booking_type"] not in [
            _t["name"] for _t in self.context.booking_types or [] if "name" in _t
        ]:
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _(
                    "Unknown booking type '${booking_type}'.",
                    mapping=dict(booking_type=data["booking_type"]),
                )
            )
            return dict(error=dict(type="Bad Request", message=msg))

        alsoProvides(self.request, IDisableCSRFProtection)

        prenotazioni_context_state = api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )
        conflict_manager = prenotazioni_context_state.conflict_manager

        if conflict_manager.conflicts(data):
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("Sorry, this slot is not available anymore.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        if exceedes_date_limit(data, self.context.getFutureDays()):
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("Sorry, you can not book this slot for now.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        booker = IBooker(self.context.aq_inner)

        book_data = {
            "booking_date": data["booking_date"],
            "booking_type": data["booking_type"],
        }
        for field in data_fields:
            book_data[field] = data_fields[field]

        # TODO: book_data ha alcuni campi che sono presenti in data
        #       con nomi diversi, va fatto un mapping tra i due
        if "fullname" in book_data:
            book_data["title"] = book_data["fullname"]

        obj = booker.create(book_data)

        if not obj:
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("Sorry, this slot is not available anymore.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        return serializer()

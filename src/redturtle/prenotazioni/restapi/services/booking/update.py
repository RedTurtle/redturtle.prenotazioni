# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.deserializer import json_body
from plone.restapi.services.content.update import ContentPatch
from redturtle.prenotazioni import _
from redturtle.prenotazioni.restapi.services.booking.additional_fields import (
    validate_booking_additional_fields,
)
from zExceptions import BadRequest

import json


class UpdateBooking(ContentPatch):
    def reply(self, *args, **kwargs):
        self.handle_additional_fields()

        return super().reply(*args, **kwargs)

    def handle_additional_fields(self):
        data = json_body(self.request)
        booking_folder = self.context.getPrenotazioniFolder()

        if data:
            # booking.additional_fields validation below
            additional_fields = data.get("additional_fields") or []

            booking_type = self.context.get_booking_type()

            # validate additional fields
            validate_booking_additional_fields(
                context=booking_folder,
                booking_type=booking_type,
                additional_fields=additional_fields,
            )

            self.request["BODY"] = json.dumps(data).encode()

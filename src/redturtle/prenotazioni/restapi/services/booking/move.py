# -*- coding: utf-8 -*-
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker
from zExceptions import BadRequest
from zope.interface import alsoProvides


class MoveBooking(Service):
    def reply(self):
        """
        @param booking_id
        @param booking_date
        @param gate (optional) -- se non definito alla move viene assegnato
                                  il gate di default (?)
        @return: 201 OK

        see: src/redturtle/prenotazioni/browser/prenotazione_move.py
        """
        data = json_body(self.request)
        booking_id = data.get("booking_id", None)
        if not booking_id:
            msg = api.portal.translate(
                _(
                    "Required input '${field}' is missing.",
                    mapping=dict(field="booking_id"),
                )
            )
            raise BadRequest(msg)

        if not data.get("booking_date"):
            msg = api.portal.translate(
                _(
                    "Required input '${field}' is missing.",
                    mapping=dict(field="booking_date"),
                )
            )
            raise BadRequest(msg)

        booking = api.content.get(UID=booking_id)

        if not booking:
            return self.reply_no_content(status=404)

        booker = IBooker(booking.getPrenotazioniFolder())

        try:
            booker.move(booking=booking, data=data)
        except BookerException as e:
            raise BadRequest(str(e))

        alsoProvides(self.request, IDisableCSRFProtection)
        # TODO: valutare se serve tornare del contenuto
        return self.reply_no_content()

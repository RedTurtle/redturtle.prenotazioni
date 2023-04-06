# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import datetimelike_to_iso
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces import IRequest


@implementer(ISerializeToJson)
@adapter(IPrenotazione, IRequest)
class PrenotazioneSerializer:
    def __init__(self, prenotazione, request):
        self.prenotazione = prenotazione
        self.reqeuest = request

    def __call__(self, *args, **kwargs):
        booking_folder = self.prenotazione.getPrenotazioniFolder()
        useful_docs = getattr(booking_folder, "cosa_serve", "")
        return {
            "title": self.prenotazione.title,
            "description": self.prenotazione.description,
            "gate": self.prenotazione.gate,
            "id": self.prenotazione.id,
            "phone": self.prenotazione.phone,
            "email": self.prenotazione.email,
            "fiscalcode": self.prenotazione.fiscalcode,
            "company": self.prenotazione.company,
            "staff_notes": self.prenotazione.staff_notes,
            "booking_date": datetimelike_to_iso(self.prenotazione.booking_date),
            "booking_expiration_date": datetimelike_to_iso(
                self.prenotazione.booking_expiration_date
            ),
            "booking_type": self.prenotazione.booking_type,
            "booking_code": self.prenotazione.getBookingCode(),
            "cosa_serve": useful_docs,
        }


# obj.__ac_local_roles__

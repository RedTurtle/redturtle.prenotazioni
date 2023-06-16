# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import datetimelike_to_iso
from plone import api
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import (
    ISerializeToPrenotazioneSearchableItem,
)
from zope.component import adapter
from zope.i18n import translate
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
            "UID": self.prenotazione.UID(),
            "@type": self.prenotazione.portal_type,
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


@implementer(ISerializeToPrenotazioneSearchableItem)
@adapter(IPrenotazione, IRequest)
class PrenotazioneSearchableItemSerializer:
    def __init__(self, prenotazione, request):
        self.prenotazione = prenotazione
        self.reqeuest = request

    def __call__(self, *args, **kwargs):
        wf_tool = api.portal.get_tool("portal_workflow")
        status = wf_tool.getStatusOf("prenotazioni_workflow", self.prenotazione)

        return {
            "booking_id": self.prenotazione.UID(),
            "booking_code": self.prenotazione.getBookingCode(),
            "booking_url": self.prenotazione.absolute_url(),
            "booking_date": datetimelike_to_iso(self.prenotazione.booking_date),
            "booking_expiration_date": datetimelike_to_iso(
                self.prenotazione.booking_expiration_date
            ),
            "booking_type": self.prenotazione.booking_type,
            # "booking_room": None,
            "booking_gate": self.prenotazione.gate,
            "booking_status": status["review_state"],
            "booking_status_label": translate(
                status["review_state"], context=self.reqeuest
            ),
            "booking_status_date": datetimelike_to_iso(status["time"]),
            "booking_status_notes": status["comments"],
            "email": self.prenotazione.email,
            "fiscalcode": self.prenotazione.fiscalcode,
            "phone": self.prenotazione.phone,
            "staff_notes": self.prenotazione.staff_notes,
            "company": self.prenotazione.company,
        }

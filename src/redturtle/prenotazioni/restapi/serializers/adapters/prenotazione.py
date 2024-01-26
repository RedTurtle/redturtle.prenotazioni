# -*- coding: utf-8 -*-
import json

from plone import api
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import json_compatible
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError
from zope.publisher.interfaces import IRequest
from zope.schema import getFields

from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.content.prenotazione_type import IPrenotazioneType
from redturtle.prenotazioni.interfaces import ISerializeToPrenotazioneSearchableItem


@implementer(ISerializeToJson)
@adapter(IPrenotazione, IRequest)
class PrenotazioneSerializer:
    def __init__(self, prenotazione, request):
        self.prenotazione = prenotazione
        self.request = request

    def __call__(self, *args, **kwargs):
        booking_folder = self.prenotazione.getPrenotazioniFolder()
        try:
            requirements = getMultiAdapter(
                (
                    getFields(IPrenotazioneType)["requirements"],
                    self.prenotazione.get_booking_type(),
                    self.request,
                ),
                IFieldSerializer,
            )()
        except ComponentLookupError:
            requirements = ""

        if self.prenotazione.fiscalcode:
            fiscalcode = self.prenotazione.fiscalcode.upper()
        else:
            fiscalcode = None

        status = api.portal.get_tool("portal_workflow").getStatusOf(
            "prenotazioni_workflow", self.prenotazione
        )
        booking_date = self.prenotazione.booking_date
        booking_expiration_date = self.prenotazione.booking_expiration_date
        if (
            booking_expiration_date
            and booking_date.date() != booking_expiration_date.date()
        ):
            logger.warning("Booking date and expiration date are different, fixing")
            booking_date = booking_date.date()
            booking_expiration_date = booking_expiration_date.replace(
                booking_date.year, booking_date.month, booking_date.day
            )
        return {
            "@id": self.prenotazione.absolute_url(),
            "UID": self.prenotazione.UID(),
            "@type": self.prenotazione.portal_type,
            "title": self.prenotazione.title,
            "description": self.prenotazione.description,
            "gate": self.prenotazione.gate,
            "id": self.prenotazione.id,
            "phone": self.prenotazione.phone,
            "email": self.prenotazione.email,
            "fiscalcode": fiscalcode,
            "company": self.prenotazione.company,
            "staff_notes": self.prenotazione.staff_notes,
            "booking_date": json_compatible(booking_date),
            "booking_expiration_date": json_compatible(booking_expiration_date),
            "booking_status": status["review_state"],
            "booking_status_label": translate(
                status["review_state"], context=self.request
            ),
            "booking_type": self.prenotazione.booking_type,
            "booking_folder_uid": booking_folder.UID(),
            "vacation": self.prenotazione.isVacation(),
            "booking_code": self.prenotazione.getBookingCode(),
            "notify_on_confirm": booking_folder.notify_on_confirm,
            "cosa_serve": requirements,  # BBB
            "requirements": requirements,
            "modification_date": json_compatible(self.prenotazione.modified()),
            "creation_date": json_compatible(self.prenotazione.created()),
        }


@implementer(ISerializeToPrenotazioneSearchableItem)
@adapter(IPrenotazione, IRequest)
class PrenotazioneSearchableItemSerializer:
    def __init__(self, prenotazione, request):
        self.prenotazione = prenotazione
        self.request = request

    def __call__(self, *args, **kwargs):
        wf_tool = api.portal.get_tool("portal_workflow")
        status = wf_tool.getStatusOf("prenotazioni_workflow", self.prenotazione)
        data = {
            "title": self.prenotazione.Title(),
            "description": self.prenotazione.description,
            "booking_id": self.prenotazione.UID(),
            "booking_code": self.prenotazione.getBookingCode(),
            "booking_url": self.prenotazione.absolute_url(),
            "booking_date": json_compatible(self.prenotazione.booking_date),
            "booking_expiration_date": json_compatible(
                self.prenotazione.booking_expiration_date
            ),
            "booking_type": self.prenotazione.booking_type,
            # "booking_room": None,
            "booking_gate": self.prenotazione.gate,
            "booking_status": status["review_state"],
            "booking_status_label": translate(
                status["review_state"], context=self.request
            ),
            "booking_status_date": json_compatible(status["time"]),
            "booking_status_notes": status["comments"],
            "email": self.prenotazione.email,
            "fiscalcode": self.prenotazione.fiscalcode,
            "phone": self.prenotazione.phone,
            "staff_notes": self.prenotazione.staff_notes,
            "company": self.prenotazione.company,
            "vacation": self.prenotazione.isVacation(),
            "modification_date": json_compatible(self.prenotazione.modified()),
            "creation_date": json_compatible(self.prenotazione.created()),
        }
        if kwargs.get("fullobjects", False):
            try:
                requirements = getMultiAdapter(
                    (
                        getFields(IPrenotazioneType)["requirements"],
                        self.prenotazione.get_booking_type(),
                        self.request,
                    ),
                    IFieldSerializer,
                )()
            except ComponentLookupError:
                requirements = ""
            prenotazioni_folder = self.prenotazione.getPrenotazioniFolder()
            data["booking_folder"] = {
                "@id": prenotazioni_folder.absolute_url(),
                "uid": prenotazioni_folder.UID(),
                "title": prenotazioni_folder.Title(),
                "orario_di_apertura": getattr(
                    prenotazioni_folder, "orario_di_apertura", None
                ),
                "description_agenda": json_compatible(
                    prenotazioni_folder.descriptionAgenda,
                    prenotazioni_folder,
                ),
                # BBB
                "address": {},
            }
            for other in ["booking_address", "booking_office"]:
                if getattr(self.prenotazione, other, None):
                    try:
                        data[other] = json.loads(getattr(self.prenotazione, other))
                    except Exception:
                        logger.warning(
                            "%s field is not JSON serializable: %s",
                            other,
                            getattr(self.prenotazione, other),
                        )
            data["requirements"] = requirements
            data["cosa_serve"] = requirements  # BBB
        return data

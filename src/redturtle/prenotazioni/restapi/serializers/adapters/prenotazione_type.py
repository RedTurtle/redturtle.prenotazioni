# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.serializer.converters import json_compatible
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione_type import IPrenotazioneType
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.interfaces import ISerializeToRetroCompatibleJson


@implementer(ISerializeToRetroCompatibleJson)
@adapter(IPrenotazioneType, IRedturtlePrenotazioniLayer)
class PrenotazioneTypeRetroCompatibleSerializer:
    """PrenotazioneType c.t. serializer retrocompatible with earlier frontend implementation"""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, *args, **kwargs):
        hidden = api.content.get_state(self.context) not in ("published",)
        return {
            "name": self.context.title,
            "duration": str(self.context.duration),
            "hidden": hidden,
            "booking_details_help_text": json_compatible(
                self.context.booking_details_help_text, self.context
            ),
            "booking_additional_fields_schema": json_compatible(
                self.context.booking_additional_fields_schema
            ),
        }

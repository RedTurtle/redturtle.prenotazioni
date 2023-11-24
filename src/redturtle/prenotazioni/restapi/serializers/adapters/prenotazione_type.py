# -*- coding: utf-8 -*-
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
        return {
            "name": self.context.title,
            "duration": str(self.context.duration),
        }

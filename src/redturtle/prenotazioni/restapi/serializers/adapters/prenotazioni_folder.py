# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.interfaces import ISerializeToRetroCompatibleJson


@implementer(ISerializeToJson)
@adapter(IPrenotazioniFolder, IRedturtlePrenotazioniLayer)
class PrenotazioniFolderSerializer(SerializeFolderToJson):
    def __call__(self, *args, **kwargs):
        res = super().__call__()

        res["booking_types"] = [
            getMultiAdapter((i, self.request), ISerializeToRetroCompatibleJson)()
            for i in self.context.get_booking_types()
        ]

        return res

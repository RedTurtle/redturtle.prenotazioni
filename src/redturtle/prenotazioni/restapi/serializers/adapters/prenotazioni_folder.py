# -*- coding: utf-8 -*-
from copy import deepcopy

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer


@implementer(ISerializeToJson)
@adapter(IPrenotazioniFolder, IRedturtlePrenotazioniLayer)
class PrenotazioniFolderSerializer(SerializeFolderToJson):
    def __call__(self, *args, **kwargs):
        res = super().__call__()

        for index, type in enumerate(deepcopy(res.get("booking_types", {}))):
            if type.get("hidden"):
                del res["booking_types"][index]

        return res

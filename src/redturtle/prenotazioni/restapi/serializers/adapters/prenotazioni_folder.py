# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import IFieldSerializer, ISerializeToJson
from plone.restapi.serializer.converters import json_compatible
from zope.component import adapter, getMultiAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.publisher.interfaces import IRequest
from zope.schema import getFields
from plone.restapi.serializer.dxcontent import SerializeFolderToJson

from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazioni_folder import (
    IPrenotazioniFolder,
)
from redturtle.prenotazioni.interfaces import (
    ISerializeToPrenotazioneSearchableItem,
)
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer

from copy import deepcopy


@implementer(ISerializeToJson)
@adapter(IPrenotazioniFolder, IRedturtlePrenotazioniLayer)
class PrenotazioniFolderSerializer(SerializeFolderToJson):
    def __call__(self, *args, **kwargs):
        res = super().__call__()

        for index, type in enumerate(deepcopy(res.get("booking_types", {}))):
            if type.get("hidden"):
                del res["booking_types"][index]

        return res

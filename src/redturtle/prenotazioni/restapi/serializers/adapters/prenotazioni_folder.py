# -*- coding: utf-8 -*-
from plone import api
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

        if res.get("booking_types"):
            if api.user.has_permission("redturtle.prenotazioni.ViewHiddenTypes"):
                return res

            res["booking_types"] = [
                t for t in res["booking_types"] if not t.get("hidden")
            ]

        return res

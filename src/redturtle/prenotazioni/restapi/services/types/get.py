# -*- coding: utf-8 -*-
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services.types.get import TypesInfo
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder


@implementer(IExpandableElement)
@adapter(IPrenotazioniFolder, Interface)
class TypesInfoPrenotazioniFolder(TypesInfo):
    """
    Custom class
    """

    def __call__(self, expand=False):
        """
        Do not show PrenotazioniYear in add menu
        """
        result = super().__call__(expand=expand)
        if not expand:
            return result
        for type_info in result["types"]:
            if type_info["id"] == "PrenotazioniYear":
                type_info["addable"] = False
                type_info["immediately_addable"] = False
        return result

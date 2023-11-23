# -*- coding: utf-8 -*-
from Acquisition import aq_chain
from Acquisition import aq_inner

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.content.prenotazioni_folder import PrenotazioniFolder


# Camel case due to legacy
def getPrenotazioniFolder(context) -> PrenotazioniFolder:
    """Retrieve PrenotazioniFolder from the content Acquisition chain"""
    if IPrenotazioniFolder.providedBy(context):
        return context

    for i in aq_chain(aq_inner(context)):
        if IPrenotazioniFolder.providedBy(i):
            return i

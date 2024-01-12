# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory

from redturtle.prenotazioni.vocabularies.voc_ore_inizio import VocOreInizio


@implementer(IVocabularyFactory)
class VocPauseScheduler(VocOreInizio):
    """Pause interval values"""

    HOURS = [f"{i:02}" for i in range(7, 21)]
    MINUTES = [f"{i:02}" for i in range(0, 60, 5)]


VocPauseScheduler = VocPauseScheduler()

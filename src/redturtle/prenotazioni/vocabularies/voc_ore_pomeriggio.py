# -*- coding: utf-8 -*-
from redturtle.prenotazioni.vocabularies.voc_ore_inizio import VocOreInizio
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory


@implementer(IVocabularyFactory)
class VocOrePomeriggio(VocOreInizio):
    """ """

    HOURS = [f"{i:02}" for i in range(14, 21)]

    def __call__(self, context):
        return super(VocOrePomeriggio, self).__call__(context)


VocOrePomeriggioFactory = VocOrePomeriggio()

# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni import _
from redturtle.prenotazioni.utils import getPrenotazioniFolder


@implementer(IVocabularyFactory)
class VocPrenotazioneTypeGatesFactory(object):
    """ """

    def __call__(self, context):
        terms = [SimpleTerm(value="all", token="all", title=_("all", default="All"))]

        for i in getattr(getPrenotazioniFolder(context), "gates", []):
            terms.append(SimpleTerm(value=i, token=i, title=i))

        return SimpleVocabulary(terms)


VocPrenotazioneTypeGatesFactory = VocPrenotazioneTypeGatesFactory()

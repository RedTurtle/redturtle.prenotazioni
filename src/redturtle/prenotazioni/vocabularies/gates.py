# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class GatesVocabulary(object):
    def __call__(self, context):
        """
        Return all the gates defined in the PrenotazioniFolder
        """
        gates = context.getGates() or []
        return SimpleVocabulary(
            [SimpleTerm(gate, str(i), gate) for i, gate in enumerate(gates)]
        )


GatesVocabularyFactory = GatesVocabulary()

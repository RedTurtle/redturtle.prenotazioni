# -*- coding: utf-8 -*-
import os
import re

from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class VocPrenotazioneTypeGatesFactory(object):
    """ """

    def __call__(self, context):
        terms = []

        myPattern = re.compile(r"REDTURTLE_PRENOTAZIONI_APPIO_KEY_\w+")

        for key in os.environ.keys():
            if myPattern.match(key):
                terms.append(
                    SimpleTerm(
                        value=key,
                        token=key,
                        title=key.replace("REDTURTLE_PRENOTAZIONI_APPIO_KEY_", ""),
                    )
                )

        return SimpleVocabulary(terms)


VocPrenotazioneTypeGatesFactory = VocPrenotazioneTypeGatesFactory()

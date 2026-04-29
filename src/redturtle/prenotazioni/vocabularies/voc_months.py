# -*- coding: utf-8 -*-
from plone import api
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

MONTH_MESSAGE_IDS = (
    "month_jan",
    "month_feb",
    "month_mar",
    "month_apr",
    "month_may",
    "month_jun",
    "month_jul",
    "month_aug",
    "month_sep",
    "month_oct",
    "month_nov",
    "month_dec",
)


@implementer(IVocabularyFactory)
class VocMonths(object):
    """Vocabulary of localized month names."""

    def __call__(self, context):
        terms = [
            SimpleTerm(
                value=index,
                token=index,
                title=api.portal.translate(msgid=msgid, domain="plonelocales"),
            )
            for index, msgid in enumerate(MONTH_MESSAGE_IDS, start=1)
        ]
        return SimpleVocabulary(terms)


VocMonthsFactory = VocMonths()

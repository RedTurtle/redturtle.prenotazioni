# -*- coding: utf-8 -*-
from plone import api
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class VocMonths(object):
    """ """

    def __call__(self, context):
        terms = [
            SimpleTerm(
                value=1,
                token=1,
                title=api.portal.translate(msgid="month_jan", domain="plonelocales"),
            ),
            SimpleTerm(
                value=2,
                token=2,
                title=api.portal.translate(msgid="month_feb", domain="plonelocales"),
            ),
            SimpleTerm(
                value=3,
                token=3,
                title=api.portal.translate(msgid="month_mar", domain="plonelocales"),
            ),
            SimpleTerm(
                value=4,
                token=4,
                title=api.portal.translate(msgid="month_apr", domain="plonelocales"),
            ),
            SimpleTerm(
                value=5,
                token=5,
                title=api.portal.translate(msgid="month_may", domain="plonelocales"),
            ),
            SimpleTerm(
                value=6,
                token=6,
                title=api.portal.translate(msgid="month_jun", domain="plonelocales"),
            ),
            SimpleTerm(
                value=7,
                token=7,
                title=api.portal.translate(msgid="month_jul", domain="plonelocales"),
            ),
            SimpleTerm(
                value=8,
                token=8,
                title=api.portal.translate(msgid="month_aug", domain="plonelocales"),
            ),
            SimpleTerm(
                value=9,
                token=9,
                title=api.portal.translate(msgid="month_sep", domain="plonelocales"),
            ),
            SimpleTerm(
                value=10,
                token=10,
                title=api.portal.translate(msgid="month_oct", domain="plonelocales"),
            ),
            SimpleTerm(
                value=11,
                token=11,
                title=api.portal.translate(msgid="month_nov", domain="plonelocales"),
            ),
            SimpleTerm(
                value=12,
                token=12,
                title=api.portal.translate(msgid="month_dec", domain="plonelocales"),
            ),
        ]
        return SimpleVocabulary(terms)


VocMonthsFactory = VocMonths()

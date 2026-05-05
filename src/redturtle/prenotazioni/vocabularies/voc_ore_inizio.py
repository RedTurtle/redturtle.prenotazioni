# -*- coding: utf-8 -*-
from plone.dexterity.interfaces import IDexterityContent
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class VocabItem(object):
    def __init__(self, token, value):
        self.token = token
        self.value = value


@implementer(IVocabularyFactory)
class VocOreInizio(object):
    """ """

    HOURS = [f"{i:02}" for i in range(7, 21)]
    MINUTES = [f"{i:02}" for i in range(0, 60, 5)]

    def __call__(self, context):
        items = []
        for hour in self.HOURS:
            for minute in self.MINUTES:
                time = hour + ":" + minute
                items.append(VocabItem(hour + minute, time))

        if not IDexterityContent.providedBy(context):
            req = getRequest()
            context = req.PARENTS[0]

        terms = []
        for item in items:
            terms.append(
                SimpleTerm(value=item.token, token=str(item.token), title=item.value)
            )
        return SimpleVocabulary(terms)


VocOreInizioFactory = VocOreInizio()

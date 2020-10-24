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
    """
    """

    HOURS = [
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
    ]
    MINUTES = ["00", "15", "30", "45"]

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
                SimpleTerm(
                    value=item.token, token=str(item.token), title=item.value
                )
            )
        return SimpleVocabulary(terms)


VocOreInizioFactory = VocOreInizio()

# -*- coding: utf-8 -*-

# from plone import api
from plone.dexterity.interfaces import IDexterityContent
from six.moves import range
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class VocabItem:
    def __init__(self, token, value):
        self.token = token
        self.value = value


@implementer(IVocabularyFactory)
class VocDurataIncontro:
    """La durata dell'incontro è espressa in minuti, e può essere compresa tra
    5 minuti e 12 ore (720 minuti).
    La durata deve essere un multiplo di 5 minuti fino a 3 ore (180 minuti), e
    un multiplo di 30 minuti da 3 ore a 12 ore.
    """

    def __call__(self, context):
        items = [VocabItem(x, x) for x in range(5, 185, 5)] + [
            VocabItem(x, x) for x in range(210, 12 * 60, 30)
        ]

        if not IDexterityContent.providedBy(context):
            req = getRequest()
            context = req.PARENTS[0]

        terms = []
        for item in items:
            terms.append(
                SimpleTerm(
                    value=str(item.token),
                    token=str(item.token),
                    title=item.value,
                )
            )
        return SimpleVocabulary(terms)


VocDurataIncontroFactory = VocDurataIncontro()

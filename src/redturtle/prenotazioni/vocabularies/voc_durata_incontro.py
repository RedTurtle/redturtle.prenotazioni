# -*- coding: utf-8 -*-

# from plone import api
from plone.dexterity.interfaces import IDexterityContent
from six.moves import range
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
class VocDurataIncontro(object):
    """
    """

    def __call__(self, context):
        items = [VocabItem(str(x), str(x)) for x in range(10, 95, 5)]

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


VocDurataIncontroFactory = VocDurataIncontro()

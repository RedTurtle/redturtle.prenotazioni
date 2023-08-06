# -*- coding: utf-8 -*-
from plone.dexterity.interfaces import IDexterityContent
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from datetime import time, timezone, datetime


class VocabItem(object):
    def __init__(self, token, value):
        self.token = token
        self.value = value


# NOTE: I thik we also need VocOreFine to follow the naming or change the naming
@implementer(IVocabularyFactory)
class VocOreInizio(object):
    """ """

    SCHEDULER = []

    def __init__(self, *args, **kwargs):
        # from 07:00 to 20:00, every 15 minutes
        for hour in range(7, 20 + 1):
            for minute in range(0, 45 + 1, 15):
                self.SCHEDULER.append(
                    # TODO: We may need to refactor this, but for now it is the only way
                    # this time to be serializer
                    datetime.combine(
                        datetime(1970, 1, 1),
                        time(hour=hour, minute=minute, tzinfo=timezone.utc),
                    )
                )

        return super().__init__(*args, **kwargs)

    def __call__(self, context):
        items = []
        for i in self.SCHEDULER:
            token = i.strftime("%H:%M")
            items.append(VocabItem(token, i))

        if not IDexterityContent.providedBy(context):
            req = getRequest()
            context = req.PARENTS[0]

        terms = []
        for item in items:
            terms.append(
                SimpleTerm(
                    value=item.value, token=item.token, title=item.token
                )
            )
        return SimpleVocabulary(terms)


VocOreInizioFactory = VocOreInizio()

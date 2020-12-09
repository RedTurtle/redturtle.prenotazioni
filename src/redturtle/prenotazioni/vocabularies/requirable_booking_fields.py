# -*- coding: utf-8 -*-
from redturtle.prenotazioni.browser.prenotazione_add import IAddForm
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import implementer


@implementer(IVocabularyFactory)
class RequirableBookingFieldsVocabulary(object):

    static_voc = SimpleVocabulary(
        [
            SimpleTerm(field, field, IAddForm[field].title)
            for field in ("email", "phone", "fiscalcode", "agency", "subject")
        ]
    )

    def __call__(self, context):
        """
        Return all the gates defined in the PrenotazioniFolder
        """
        return self.static_voc


RequirableBookingFieldsVocabularyFactory = RequirableBookingFieldsVocabulary()

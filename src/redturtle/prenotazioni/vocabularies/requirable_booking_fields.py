# -*- coding: utf-8 -*-
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import implementer
from redturtle.prenotazioni.config import REQUIRABLE_AND_VISIBLE_FIELDS
from zope.i18n import translate
from redturtle.prenotazioni import _


@implementer(IVocabularyFactory)
class RequirableBookingFieldsVocabulary(object):
    def __call__(self, context):
        """
        Return all the gates defined in the PrenotazioniFolder
        """
        return SimpleVocabulary(
            [
                SimpleTerm(
                    field,
                    field,
                    translate(
                        _("label_booking_{}".format(field)), context=context.REQUEST
                    ),
                )
                for field in REQUIRABLE_AND_VISIBLE_FIELDS
            ]
        )


RequirableBookingFieldsVocabularyFactory = RequirableBookingFieldsVocabulary()

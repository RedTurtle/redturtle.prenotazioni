# -*- coding: utf-8 -*-
from zope.i18n import translate
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni import _
from redturtle.prenotazioni.config import REQUIRABLE_AND_VISIBLE_FIELDS


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

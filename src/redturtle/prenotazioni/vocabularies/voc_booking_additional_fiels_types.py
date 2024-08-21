# -*- coding: utf-8 -*-
from zope.i18n import translate
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni import _
from redturtle.prenotazioni.config import BOOKING_ADDITIONAL_FIELDS_TYPES


@implementer(IVocabularyFactory)
class BookingAdditionalFieldsTypesVocabulary(object):
    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm(
                    field,
                    field,
                    translate(
                        _("label_booking_additional_field{}".format(field)),
                        context=context.REQUEST,
                    ),
                )
                for field in BOOKING_ADDITIONAL_FIELDS_TYPES
            ]
        )


BookingAdditionalFieldsTypesVocabularyFactory = BookingAdditionalFieldsTypesVocabulary()

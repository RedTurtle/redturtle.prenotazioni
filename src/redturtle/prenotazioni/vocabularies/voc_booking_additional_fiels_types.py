# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.schema import TextLine
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni import _


class SimpleTermFieldType(SimpleTerm):
    field_validator = None

    def __init__(self, *args, **kwargs):
        self.field_validator = kwargs.get("field_validator")

        if self.field_validator:
            del kwargs["field_validator"]

        return super().__init__(*args, **kwargs)


@implementer(IVocabularyFactory)
class BookingAdditionalFieldsTypesVocabulary(object):
    def __call__(self, context):
        return SimpleVocabulary(
            # Other fields may be added in the future
            [
                SimpleTermFieldType(
                    "text",
                    "text",
                    context.translate(
                        _(
                            "label_booking_additional_field_textline",
                            default="Text line",
                        )
                    ),
                    field_validator=TextLine().validate,
                )
            ]
        )


BookingAdditionalFieldsTypesVocabularyFactory = BookingAdditionalFieldsTypesVocabulary()

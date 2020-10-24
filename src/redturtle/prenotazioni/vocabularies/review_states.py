# -*- coding: utf-8 -*-
from plone import api
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory


@implementer(IVocabularyFactory)
class BookingReviewStatesVocabulary(object):
    """Vocabulary factory for workflow states of a Prenotazione
    """

    def __call__(self, context):
        prenotazioni_portal_state = api.content.get_view(
            "prenotazioni_portal_state", context, context.REQUEST
        )
        return prenotazioni_portal_state.booking_review_states


BookingReviewStatesVocabularyFactory = BookingReviewStatesVocabulary()  # noqa

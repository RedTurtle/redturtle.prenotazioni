# -*- coding: utf-8 -*-
from redturtle.prenotazioni.content.prenotazione import Prenotazione
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class BookingTypesVocabulary(object):
    def get_tipologies(self, context):
        """Return the tipologies in the PrenotazioniFolder"""
        if isinstance(context, Prenotazione):
            context = context.getPrenotazioniFolder()
        return getattr(context, "booking_types", [])

    def booking_type2term(self, idx, booking_type):
        """return a vocabulary tern with this"""
        idx = str(idx)
        name = booking_type.get("name", "")
        if isinstance(name, str):
            name = name
        duration = booking_type.get("duration", "")
        if isinstance(duration, str):
            duration = duration

        if not duration:
            title = name
        else:
            title = "%s (%s min)" % (name, duration)
        # fix for buggy implementation
        term = SimpleTerm(name, token="changeme", title=title)
        term.token = name
        return term

    def get_terms(self, context):
        """The vocabulary terms"""
        return [
            self.booking_type2term(idx, booking_type)
            for idx, booking_type in enumerate(self.get_tipologies(context))
        ]

    def __call__(self, context):
        """
        Return all the tipologies defined in the PrenotazioniFolder
        """
        return SimpleVocabulary(self.get_terms(context))


BookingTypesVocabularyFactory = BookingTypesVocabulary()

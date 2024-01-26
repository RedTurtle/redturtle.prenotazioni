# -*- coding: utf-8 -*-
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni.utils.get_prenotazioni_folder import getPrenotazioniFolder


@implementer(IVocabularyFactory)
class PrenotazioneTypesVocabulary(object):
    def booking_type2term(self, booking_type):
        """return a vocabulary tern with this"""
        name = booking_type.title
        duration = booking_type.duration

        if not duration:
            title = name
        else:
            title = f"{name} ({duration} min)"

        return SimpleTerm(name, token=name, title=title)

    def get_terms(self, context):
        """The vocabulary terms"""
        prenotazioni_folder = getPrenotazioniFolder(context)

        return [
            self.booking_type2term(booking_type)
            for booking_type in prenotazioni_folder
            and prenotazioni_folder.get_booking_types()
            or []
        ]

    def __call__(self, context):
        """
        Return all the tipologies defined in the PrenotazioniFolder
        """
        if IPloneSiteRoot.providedBy(context):
            catalog = api.portal.get_tool("portal_catalog")
            return SimpleVocabulary(
                [
                    self.booking_type2term(brain.getObject())
                    for brain in catalog(
                        portal_type="PrenotazioneType", sort_by="sortable_title"
                    )
                ]
            )
        else:
            return SimpleVocabulary(self.get_terms(context))


PrenotazioneTypesVocabularyFactory = PrenotazioneTypesVocabulary()

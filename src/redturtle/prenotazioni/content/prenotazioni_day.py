# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IPrenotazioniDay(model.Schema):
    """ Marker interface and Dexterity Python Schema for PrenotazioniDay
    """

@implementer(IPrenotazioniDay)
class PrenotazioniDay(Container):
    """
    """
    exclude_from_nav = True

    def email_responsabile(self):
        return aq_parent(aq_parent(aq_parent(aq_inner(self)))).email_responsabile

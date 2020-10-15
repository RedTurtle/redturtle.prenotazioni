# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IPrenotazioniWeek(model.Schema):
    """ Marker interface and Dexterity Python Schema for PrenotazioniWeek
    """


@implementer(IPrenotazioniWeek)
class PrenotazioniWeek(Container):
    """
    """
    exclude_from_nav = True

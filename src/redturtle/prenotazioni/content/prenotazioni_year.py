# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IPrenotazioniYear(model.Schema):
    """ Marker interface and Dexterity Python Schema for PrenotazioniYear
    """


@implementer(IPrenotazioniYear)
class PrenotazioniYear(Container):
    """
    """

    exclude_from_nav = True

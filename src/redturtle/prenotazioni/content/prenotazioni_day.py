# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IPrenotazioniDay(model.Schema):
    """Marker interface and Dexterity Python Schema for PrenotazioniDay"""


@implementer(IPrenotazioniDay)
class PrenotazioniDay(Container):
    """ """

    exclude_from_nav = True

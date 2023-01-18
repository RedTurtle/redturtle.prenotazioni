# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.interface.interfaces import IObjectEvent
from zope.interface.interfaces import ObjectEvent


class IMovedPrenotazione(IObjectEvent):

    """Marker interface for prenotazione that is moved"""


@implementer(IMovedPrenotazione)
class MovedPrenotazione(ObjectEvent):

    """Event fired when a prenotazione that is moved"""

    def __init__(self, obj):
        super(MovedPrenotazione, self).__init__(obj)

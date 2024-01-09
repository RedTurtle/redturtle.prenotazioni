# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent


class IMovedPrenotazione(IObjectModifiedEvent):

    """Marker interface for prenotazione that is moved"""


@implementer(IMovedPrenotazione)
class MovedPrenotazione(ObjectModifiedEvent):

    """Event fired when a prenotazione that is moved"""

    def __init__(self, obj):
        super(MovedPrenotazione, self).__init__(obj)

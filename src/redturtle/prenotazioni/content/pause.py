# -*- coding: utf-8 -*-
from zope.interface import implementer
from redturtle.prenotazioni.interfaces import IPause
from datetime import datetime
from redturtle.prenotazioni.config import PAUSE_PORTAL_TYPE
from redturtle.prenotazioni import _


@implementer(IPause)
class Pause(object):
    """
    A dummy object to allow pause to be ISlot adaptable. We don't have a
    reservation date and we don't need it. Consider that we pass these
    information to a method that take a date and return the number of seconds
    from 00:00. So we can use epoch date (1970/01/01) appending pause starts
    and pause ends.
    We provide in this class the two method used by ISlot adapter to allow
    ISlot handle pause the same way they handle bookings
    """

    def __init__(self, start, stop, gate=""):
        """
        :param start: the hour the pause starts
        :param stop: the hour the pause ends
        :param gate: the gate involved in this pause. Maybe we use it in future
        """
        self.start = start
        self.stop = stop
        self.gate = gate

    @property
    def portal_type(self):
        return PAUSE_PORTAL_TYPE

    @property
    def is_pause(self):
        return True

    @property
    def Title(self):
        return _("Pause")

    def getData_prenotazione(self):
        # we use as base date 1970/01/01
        # we pass these data to a method that convert it to a day agnostic
        # number
        return datetime.strptime(
            "1970/01/01 {}".format(self.start), "%Y/%m/%d %H:%M"
        )

    def getData_scadenza(self):
        # we use as base date 1970/01/01
        # we pass these data to a method that convert it to a day agnostic
        # number
        return datetime.strptime(
            "1970/01/01 {}".format(self.stop), "%Y/%m/%d %H:%M"
        )

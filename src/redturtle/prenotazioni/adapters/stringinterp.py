# -*- coding: utf-8 -*-
from plone.stringinterp.adapters import BaseSubstitution
from redturtle.prenotazioni import _
from zope.component import adapter
from zope.interface import Interface


@adapter(Interface)
class GateSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The gate booked.")

    def safe_call(self):
        return getattr(self.context, "gate", "")


@adapter(Interface)
class BookingDateSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booked date.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_prenotazione", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date)


@adapter(Interface)
class BookingTimeSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booked time.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_prenotazione", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date, time_only=True)


@adapter(Interface)
class BookingTypeSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking type.")

    def safe_call(self):
        return getattr(self.context, "tipologia_prenotazione", "")

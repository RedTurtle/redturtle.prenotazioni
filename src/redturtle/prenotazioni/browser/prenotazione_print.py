# -*- coding: utf-8 -*-
from plone.memoize.view import memoize
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from redturtle.prenotazioni import _
from redturtle.prenotazioni.utilities.urls import urlify
from plone.protect.utils import addTokenToUrl


class PrenotazionePrint(BrowserView):

    """
    This is a view to proxy autorizzazione
    """

    print_action = "javascript:this.print();"

    description = _(
        "confirm_booking_waiting_message",
        u"Your booking has to be confirmed by the administrators",
    )

    @property
    @memoize
    def label(self):
        """ The lable of this view
        """
        title = self.prenotazione.getPrenotazioniFolder().Title()  # noqa
        return _(
            "reservation_request",
            u"Booking request for: ${name}",
            mapping={"name": title},
        )

    @property
    @memoize
    def prenotazione(self):
        """
        Get's the prenotazione by uid
        """
        uid = self.request.get("uid")
        if not uid:
            return
        pc = getToolByName(self.context, "portal_catalog")
        query = {"portal_type": "Prenotazione", "UID": uid}
        brains = pc.unrestrictedSearchResults(query)
        if len(brains) != 1:
            return None

        return brains[0]._unrestrictedGetObject()

    def __call__(self):
        """
        Se non c'e' la prenotazione vai all'oggetto padre
        """
        if not self.prenotazione:
            qs = {}
            data = self.request.get("data")
            if data:
                qs["data"] = data
            msg = "Not found"
            IStatusMessage(self.request).add(msg, "warning")
            target = urlify(self.context.absolute_url(), params=qs)
            return self.request.response.redirect(target)
        else:
            return super(PrenotazionePrint, self).__call__()

    def protect_url(self, url):
        return addTokenToUrl(url)

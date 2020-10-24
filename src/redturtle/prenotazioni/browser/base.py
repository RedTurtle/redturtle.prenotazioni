# -*- coding: utf-8 -*-
from plone import api
from plone.memoize.view import memoize
from Products.Five.browser import BrowserView
from redturtle.prenotazioni.adapters.conflict import IConflictManager
from redturtle.prenotazioni.content.prenotazioni_folder import (
    IPrenotazioniFolder,
)
from zExceptions import NotFound


class BaseView(BrowserView):
    """ base view for redturtle.prenotazioni

    Give some handy cached methods
    """

    @property
    @memoize
    def prenotazioni(self):
        """ Returns the prenotazioni_context_state view.

        Everyone should know about this!
        """
        return api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )

    @property
    @memoize
    def prenotazione_macros(self):
        """ Returns the prenotazione_macros view.

        Everyone should know about this!
        """
        return api.content.get_view(
            "prenotazione_macros", self.context, self.request
        )

    @property
    @memoize
    def conflict_manager(self):
        """
        Return the conflict manager for this context
        """
        return IConflictManager(self.context)


class RedirectToPrenotazioniFolderView(BrowserView):
    """ A view that redirects to the parent Prenotazioni Folder (if found)
    """

    def get_target_url(self):
        """ Get's the prenotazioni folder
        """
        for parent in self.context.aq_inner.aq_chain:
            if IPrenotazioniFolder.providedBy(parent):
                return parent.absolute_url()
        return ""

    def __call__(self):
        """ Redirect to prenotazioni or raise not found
        """
        target_url = self.get_target_url()
        if not target_url:
            raise NotFound("Can't find a PrenotazioniFolder container")
        return self.request.response.redirect(target_url)

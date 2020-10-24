# -*- coding: utf-8 -*-
from plone import api
from plone.memoize.view import memoize_contextless
from Products.CMFPlone import PloneMessageFactory as __
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from zope.i18n import translate
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class PrenotazioniPortalState(BrowserView):

    """ Some globals for this package
    """

    booking_types = ["Prenotazione"]

    @property
    @memoize_contextless
    def plone_tools(self):
        """
        """
        return api.content.get_view("plone_tools", self.context, self.request)

    @property
    @memoize_contextless
    def booking_review_states(self):
        """ Heavily inspired by workflowtool listWFStatesByTitle
        """
        pw = self.plone_tools.workflow()
        states = []
        dup_list = {}
        for booking_type in self.booking_types:
            wfids = pw._chains_by_type.get(booking_type)
            for wfid in wfids:
                wf = pw.getWorkflowById(wfid)
                state_folder = getattr(wf, "states", None)
                if state_folder is not None:
                    for state in state_folder.values():
                        key = "%s:%s" % (state.id, state.title)
                        if key not in dup_list:
                            states.append(state)
                        dup_list[key] = 1
        terms = []
        for state in states:
            key = state.getId()
            title = translate(
                __(safe_unicode(state.title)), context=self.request
            )
            terms.append(SimpleTerm(key, title=title))
        terms.sort(key=lambda x: x.title)
        return SimpleVocabulary(terms)

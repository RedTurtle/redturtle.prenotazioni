# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.memoize.view import memoize
from plone.z3cform.layout import wrap_form
from Products.CMFPlone import PloneMessageFactory as __
from Products.CMFPlone.browser.search import quote_chars
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.conflict import IConflictManager
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import Choice
from zope.schema import Date
from zope.schema import TextLine
from zope.schema import ValidationError
from zope.schema.interfaces import IVocabularyFactory


class InvalidDate(ValidationError):
    __doc__ = _("invalid_end:search_date", u"Invalid start or end date")


class ISearchForm(Interface):
    """
    Interface for creating a prenotazione
    """

    text = TextLine(
        title=_("label_text", u"Text to search"), default=u"", required=False
    )
    review_state = Choice(
        title=__("State"),
        default="",
        required=False,
        source="redturtle.prenotazioni.booking_review_states",
    )
    gate = Choice(
        title=_("label_gate", u"Gate"),
        default="",
        required=False,
        source="redturtle.prenotazioni.gates",
    )
    start = Date(
        title=_("label_start", u"Start date "),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )
    end = Date(
        title=_("label_end", u"End date"),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )


@implementer(ISearchForm)
class SearchForm(form.Form):

    """
    """

    ignoreContext = True
    template = ViewPageTemplateFile("templates/prenotazioni_search.pt")
    prefix = ""
    brains = []

    fields = field.Fields(ISearchForm)

    @property
    @memoize
    def conflict_manager(self):
        """
        Return the conflict manager for this context
        """
        return IConflictManager(self.context)

    @property
    @memoize
    def prenotazioni_week_view(self):
        """
        Return the conflict manager for this context
        """
        return api.content.get_view(
            "prenotazioni_week_view", self.context, self.request
        )

    def get_prenotazione_state(self, item):
        factory = getUtility(
            IVocabularyFactory, "redturtle.prenotazioni.booking_review_states"
        )
        vocabulary = factory(item)
        if not vocabulary:
            return ""
        term = vocabulary.getTerm(api.content.get_state(obj=item))
        if not term:
            return ""
        return term.title

    def get_query(self, data):
        """ The query we requested
        """
        query = {
            "sort_on": "Date",
            "sort_order": "reverse",
            "path": "/".join(self.context.getPhysicalPath()),
        }
        if data.get("text"):
            query["SearchableText"] = quote_chars(data["text"])
        if data.get("review_state"):
            query["review_state"] = data["review_state"]

        if data.get("gate"):
            factory = getUtility(
                IVocabularyFactory, "redturtle.prenotazioni.gates"
            )
            vocabulary = factory(context=self.context)
            try:
                term = vocabulary.getTermByToken(data["gate"])
                query["Subject"] = "Gate: {}".format(term.value)
            except LookupError:
                query["Subject"] = "Gate: {}".format(data["gate"])
        start = data.get("start", None)
        end = data.get("end", None)
        if start and end:
            query["Date"] = {
                "query": [
                    DateTime(start.__str__()),
                    DateTime(end.__str__()) + 1,
                ],
                "range": "min:max",
            }
        elif start:
            query["Date"] = {
                "query": DateTime(start.__str__()),
                "range": "min",
            }
        elif end:
            query["Date"] = {
                "query": DateTime(end.__str__()) + 1,
                "range": "max",
            }
        return query

    def get_brains(self, data=None):
        """
        The brains for my search
        """
        if self.request.form.get("buttons.action_search", ""):
            data, errors = self.extractData()
        else:
            data = self.request.form
        query = self.get_query(data=data)
        return self.conflict_manager.unrestricted_prenotazioni(**query)

    # Use base form validation
    # def validate(self, action, data):
    #     '''
    #     Checks if input dates are correct
    #     '''
    #     errors = super(SearchForm, self).validate(action, data)
    #     return errors
    def updateWidgets(self):
        super(SearchForm, self).updateWidgets()
        for k, v in self.request.form.items():
            if k in self.widgets:
                self.widgets[k].value = v

    @button.buttonAndHandler(_(u"action_search", default=u"Search"))
    def action_search(self, action):
        """
        Search in prenotazioni SearchableText
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

    @button.buttonAndHandler(
        _(u"move_back_message", default=u"Go back to the calendar")
    )
    def action_cancel(self, action):
        """
        Cancel and go back to the week view
        """
        target = self.context.absolute_url()
        return self.request.response.redirect(target)


WrappedSearchForm = wrap_form(SearchForm)

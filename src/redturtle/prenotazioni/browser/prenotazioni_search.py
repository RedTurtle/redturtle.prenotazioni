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
from redturtle.prenotazioni.utilities.urls import urlify
import tempfile
from pyexcel_ods3 import save_data
from ZPublisher.Iterators import filestream_iterator
from datetime import datetime
from plone.api.content import get_state


class InvalidDate(ValidationError):
    __doc__ = _("invalid_end:search_date", "Invalid start or end date")


class ISearchForm(Interface):
    """
    Interface for creating a prenotazione
    """

    text = TextLine(title=_("label_text", "Text to search"), default="", required=False)
    review_state = Choice(
        title=__("State"),
        default="",
        required=False,
        source="redturtle.prenotazioni.booking_review_states",
    )
    gate = Choice(
        title=_("label_gate", "Gate"),
        default="",
        required=False,
        source="redturtle.prenotazioni.gates",
    )
    start = Date(
        title=_("label_start", "Start date "),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )
    end = Date(
        title=_("label_end", "End date"),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )


@implementer(ISearchForm)
class SearchForm(form.Form):

    """ """

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

    def get_prenotazioni_states(self):
        factory = getUtility(
            IVocabularyFactory, "redturtle.prenotazioni.booking_review_states"
        )
        vocabulary = factory(self.context)
        if not vocabulary:
            return ""
        return {k: v.title for (k, v) in factory(self.context).by_token.items()}

    def get_query(self, data):
        """The query we requested"""
        self.query_data = {}
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
            factory = getUtility(IVocabularyFactory, "redturtle.prenotazioni.gates")
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

    def set_search_string(self, data):
        result = []
        MARKUP = "<strong>{}:</strong> {}"
        if "text" in data and data.get("text", None):
            result.append(
                MARKUP.format(
                    self.context.translate(_("label_text", "Text to search")),
                    data["text"],
                )
            )
        if "review_state" in data and data.get("review_state", None):
            result.append(
                MARKUP.format(
                    self.context.translate(
                        __("State"),
                    ),
                    self.context.translate(__(data["review_state"])),
                )
            )

        if "gate" in data and data.get("gate", None):
            result.append(
                MARKUP.format(
                    self.context.translate(
                        _("label_gate", "Gate"),
                    ),
                    data["gate"],
                )
            )

        if "start" in data and data.get("start", None):
            if isinstance(data.get("start"), str):
                data["start"] = datetime.strptime(data.get("start"), "%Y-%m-%d")
            result.append(
                MARKUP.format(
                    self.context.translate(_("label_start", "Start date ")),
                    data["start"].strftime("%d/%m/%Y"),
                )
            )

        if "end" in data and data.get("end", None):
            if isinstance(data.get("end"), str):
                data["end"] = datetime.strptime(data.get("end"), "%Y-%m-%d")
            result.append(
                MARKUP.format(
                    self.context.translate(_("label_end", "End date")),
                    data["end"].strftime("%d/%m/%Y"),
                )
            )
        search_string = ""
        if result:
            search_string = "; ".join(result)
            search_string = "<p>{}</p>".format(search_string)
        return search_string

    def set_download_url(self, data):
        return urlify(
            "{}/@@download_reservation".format(self.context.absolute_url()),
            params=data,
        )

    def get_brains(self, data=None):
        """
        The brains for my search
        """
        if self.request.form.get("buttons.action_search", ""):
            data, errors = self.extractData()
        else:
            data = self.request.form
        query = self.get_query(data=data)
        self.search_string = self.set_search_string(data)
        self.download_url = self.set_download_url(data)
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

    @button.buttonAndHandler(_("action_search", default="Search"))
    def action_search(self, action):
        """
        Search in prenotazioni SearchableText
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

    @button.buttonAndHandler(_("move_back_message", default="Go back to the calendar"))
    def action_cancel(self, action):
        """
        Cancel and go back to the week view
        """
        target = self.context.absolute_url()
        return self.request.response.redirect(target)


WrappedSearchForm = wrap_form(SearchForm)


class DownloadReservation(SearchForm):

    columns = [
        "Nome completo",
        "Stato",
        "Postazione",
        "Tipologia prenotazione",
        "Email",
        "Telefono",
        "Data prenotazione",
        "Codice prenotazione",
        "Note prenotante",
        "Note del personale",
    ]

    @memoize
    def get_prenotazioni_states(self):
        factory = getUtility(
            IVocabularyFactory, "redturtle.prenotazioni.booking_review_states"
        )
        vocabulary = factory(self.context)
        if not vocabulary:
            return ""
        return {k: v.title for (k, v) in factory(self.context).by_token.items()}

    def get_prenotazione_state(self, obj):
        states = self.get_prenotazioni_states()
        return states.get(get_state(obj), "")

    def __call__(self):
        data = {
            "sort_on": "Date",
            "sort_order": "reverse",
            "path": "/".join(self.context.getPhysicalPath()),
        }
        for k in self.request.form:
            v = self.request.form.get(k, None)
            if v and v != "None":
                data[k] = v
        if data:
            query = self.get_query(data=data)
            brains = self.conflict_manager.unrestricted_prenotazioni(**query)
        else:
            brains = []
        data = {"Sheet 1": [self.columns]}
        for brain in brains:
            data["Sheet 1"].append(self.get_row_data(brain=brain))

        now = DateTime()
        filename = "prenotazioni_{}.ods".format(now.strftime("%Y%m%d%H%M%S"))
        filepath = "{0}/{1}".format(tempfile.mkdtemp(), filename)
        save_data(filepath, data)
        streamed = filestream_iterator(filepath)
        mime = "application/vnd.oasis.opendocument.spreadsheet"
        self.request.RESPONSE.setHeader(
            "Content-type", "{0};charset={1}".format(mime, "utf-8")
        )
        self.request.RESPONSE.setHeader("Content-Length", str(len(streamed)))
        self.request.RESPONSE.setHeader(
            "Content-Disposition", 'attachment; filename="{}"'.format(filename)
        )
        return streamed

    def get_row_data(self, brain):
        obj = brain.getObject()
        return [
            brain.Title,
            self.get_prenotazione_state(obj),
            getattr(obj, "gate", "") or "",
            getattr(obj, "booking_type", "") or "",
            getattr(obj, "email", "") or "",
            getattr(obj, "phone", "") or "",
            self.prenotazioni_week_view.localized_time(brain["Date"])
            + " - "
            + self.prenotazioni_week_view.localized_time(brain["Date"], time_only=True),
            obj.getBookingCode(),
            getattr(obj, "description", "") or "",
            obj.getStaff_notes() or "",
        ]

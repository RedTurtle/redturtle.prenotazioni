# -*- coding: utf-8 -*-
from plone.z3cform.layout import wrap_form
from Products.CMFPlone import PloneMessageFactory as __

from z3c.form import button
from z3c.form import field

from zope.interface import implementer
from zope.interface import Interface
from zope.schema import Choice
from zope.schema import Date
from zope.schema import TextLine

from redturtle.prenotazioni import _
from redturtle.prenotazioni.browser.prenotazioni_search import SearchForm


class ISearchAllForm(Interface):
    """
    Interface for searching 'prenotazione' in all the portal
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
    order_by_date = Choice(
        title=_("label_order_by_date", u"Order by date"),
        description=_(
            "Descending to show more recent first, Ascending to show less recent first."
        ),
        default=("Discendente"),
        required=False,
        values=("Ascendente", "Discendente"),
    )


@implementer(ISearchAllForm)
class SearchAllForm(SearchForm):

    """ """

    fields = field.Fields(ISearchAllForm)

    @button.buttonAndHandler(_(u"action_search", default=u"Search"))
    def action_search(self, action):
        """
        Search in prenotazioni SearchableText
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return


WrappedSearchAllForm = wrap_form(SearchAllForm)

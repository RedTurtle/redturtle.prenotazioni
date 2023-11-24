# -*- coding: utf-8 -*-
import logging

from plone import api
from plone.memoize.view import memoize
from plone.protect.utils import addTokenToUrl
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import ActionExecutionError
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import implementer
from zope.schema import Datetime
from zope.schema import TextLine

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.utilities.urls import urlify

logger = logging.getLogger(__name__)


class IMoveForm(Interface):

    """
    Interface for moving a prenotazione
    """

    booking_date = Datetime(title=_("label_booking_time", "Booking time"), default=None)
    gate = TextLine(title=_("label_gate", "Gate"), default="", required=False)


@implementer(IMoveForm)
class MoveForm(form.Form):

    """Controller for moving a booking"""

    ignoreContext = True

    template = ViewPageTemplateFile("templates/prenotazione_move.pt")

    hidden_fields = []
    fields = field.Fields(IMoveForm)

    @property
    @memoize
    def prenotazioni_folder(self):
        """
        The PrenotazioniFolder object that contains the context
        """
        return self.context.getPrenotazioniFolder()

    @property
    @memoize
    def prenotazioni_view(self):
        """
        The prenotazioni_context_state view in the context
        of prenotazioni_folder
        """
        return api.content.get_view(
            "prenotazioni_context_state",
            self.prenotazioni_folder,
            self.request,
        )

    # @memoize se usato rompre la vista
    def slot_styles(self, slot):
        """
        Return a css to underline the moved slot
        """
        context = slot.context
        if not context:
            return "links"
        styles = [self.prenotazioni_view.get_state(context)]
        if context == self.context:
            styles.append("links")
        return " ".join(styles)

    @property
    @memoize
    def back_to_booking_url(self):
        """This goes back to booking view."""
        qs = {"data": (self.context.getBooking_date().strftime("%d/%m/%Y"))}
        return urlify(self.prenotazioni_folder.absolute_url(), params=qs)

    # @memoize se usato rompe la vista
    def move_to_slot_links(self, day, slot, gate):
        """
        Returns the url to move the booking in this slot
        """
        if not self.prenotazioni_view.is_valid_day(day):
            return []
        if self.prenotazioni_view.maximum_bookable_date:
            if day > self.prenotazioni_view.maximum_bookable_date.date():
                return []
        date = day.strftime("%Y-%m-%d")
        params = {
            "form.buttons.action_move": "Move",
            "data": self.request.form.get("data", ""),
            "form.widgets.gate": gate,
        }
        times = slot.get_values_hr_every(300)
        urls = []
        base_url = "/".join((self.context.absolute_url(), "prenotazione_move"))
        now_str = tznow()
        for t in times:
            booking_date_str = "T".join((date, t))
            booking_date = datetime_with_tz(booking_date_str)
            params["form.widgets.booking_date"] = booking_date_str
            urls.append(
                {
                    "title": t,
                    "url": addTokenToUrl(urlify(base_url, params=params)),
                    "class": t.endswith(":00") and "oclock" or None,
                    "future": (now_str <= booking_date),
                }
            )
        return urls

    @button.buttonAndHandler(_("action_move", "Move"))
    def action_move(self, action):
        """
        Book this resource

        # TODO: codice replicato in services/booking/move.py
        """
        data, errors = self.extractData()
        booker = IBooker(self.prenotazioni_folder)
        try:
            booker.move(booking=self.context, data=data)
        except BookerException as e:
            api.portal.show_message(e.args[0], self.request, type="error")
            raise ActionExecutionError(Invalid(e.args[0]))

        msg = _("booking_moved")
        api.portal.show_message(msg, self.request, type="info")
        booking_date = data["booking_date"].strftime("%d/%m/%Y")
        target = urlify(
            self.prenotazioni_folder.absolute_url(),
            paths=["prenotazioni_week_view"],
            params={"data": booking_date},
        )
        return self.request.response.redirect(target)

    @button.buttonAndHandler(_("action_cancel", "Cancel"))
    def action_cancel(self, action):
        """
        Cancel
        """
        target = self.back_to_booking_url
        return self.request.response.redirect(target)

    def __call__(self):
        """Hide the portlets before serving the template"""
        self.request.set("disable_plone.leftcolumn", 1)
        self.request.set("disable_plone.rightcolumn", 1)
        return super(MoveForm, self).__call__()

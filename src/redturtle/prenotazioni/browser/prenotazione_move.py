# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.memoize.view import memoize
from plone.protect.utils import addTokenToUrl
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.prenotazione_event import MovedPrenotazione
from redturtle.prenotazioni.utilities.urls import urlify
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import ActionExecutionError
from zope.event import notify
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import Datetime
from zope.schema import TextLine


class IMoveForm(Interface):

    """
    Interface for moving a prenotazione
    """

    booking_date = Datetime(
        title=_("label_booking_time", u"Booking time"), default=None
    )
    gate = TextLine(
        title=_("label_gate", u"Gate"), default=u"", required=False
    )


@implementer(IMoveForm)
class MoveForm(form.Form):

    """ Controller for moving a booking
    """

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

    def exceedes_date_limit(self, data):
        """
        Check if we can book this slot or is it too much in the future.
        """
        future_days = self.context.getFutureDays()
        if not future_days:
            return False
        booking_date = data.get("booking_date", None)
        if not isinstance(booking_date, datetime):
            return False
        date_limit = tznow() + timedelta(future_days)
        if booking_date <= date_limit:
            return False
        return True

    def do_move(self, data):
        """
        Move a Booking!
        """
        booking_date = data["booking_date"]
        duration = self.context.getDuration()
        data_scadenza = booking_date + duration
        self.context.setData_prenotazione(booking_date)
        self.context.setData_scadenza(data_scadenza)
        self.context.gate = data["gate"] or ""
        self.context.reindexObject(idxs=["Subject"])
        notify(MovedPrenotazione(self.context))

    @property
    @memoize
    def back_to_booking_url(self):
        """ This goes back to booking view.
        """
        qs = {
            "data": (self.context.getData_prenotazione().strftime("%d/%m/%Y"))
        }
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
        now_str = tznow().strftime("%Y-%m-%d %H:%M")
        for t in times:
            form_booking_date = " ".join((date, t))
            params["form.widgets.booking_date"] = form_booking_date
            urls.append(
                {
                    "title": t,
                    "url": addTokenToUrl(urlify(base_url, params=params)),
                    "class": t.endswith(":00") and "oclock" or None,
                    "future": (now_str <= form_booking_date),
                }
            )
        return urls

    @button.buttonAndHandler(_(u"action_move", u"Move"))
    def action_move(self, action):
        """
        Book this resource
        """
        data, errors = self.extractData()
        data["tipology"] = self.context.getTipologia_prenotazione()
        conflict_manager = self.prenotazioni_view.conflict_manager
        current_data = self.context.getData_prenotazione()
        current = {"booking_date": current_data, "tipology": data["tipology"]}
        current_slot = conflict_manager.get_choosen_slot(current)
        current_gate = getattr(self.context, "gate", "")
        exclude = {current_gate: [current_slot]}

        if conflict_manager.conflicts(data, exclude=exclude):
            msg = _(
                u"Sorry, this slot is not available or does not fit your "
                u"booking."
            )
            api.portal.show_message(msg, self.request, type="error")
            raise ActionExecutionError(Invalid(msg))
        if self.exceedes_date_limit(data):
            msg = _(u"Sorry, you can not book this slot for now.")
            api.portal.show_message(msg, self.request, type="error")
            raise ActionExecutionError(Invalid(msg))

        obj = self.do_move(data)
        obj  # pyflakes
        msg = _("booking_moved")
        IStatusMessage(self.request).add(msg, "info")
        booking_date = data["booking_date"].strftime("%d/%m/%Y")
        target = urlify(
            self.prenotazioni_folder.absolute_url(),
            paths=["prenotazioni_week_view"],
            params={"data": booking_date},
        )
        return self.request.response.redirect(target)

    @button.buttonAndHandler(_(u"action_cancel", u"Cancel"))
    def action_cancel(self, action):
        """
        Cancel
        """
        target = self.back_to_booking_url
        return self.request.response.redirect(target)

    def __call__(self):
        """ Hide the portlets before serving the template
        """
        self.request.set("disable_plone.leftcolumn", 1)
        self.request.set("disable_plone.rightcolumn", 1)
        return super(MoveForm, self).__call__()

# -*- coding: utf-8 -*-
from datetime import datetime
from DateTime import DateTime
from plone import api
from plone.memoize.view import memoize
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from redturtle.prenotazioni import _
from redturtle.prenotazioni import prenotazioniLogger as logger
from redturtle.prenotazioni import time2timedelta
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.utilities.urls import urlify
from six.moves import map
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import ActionExecutionError
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import Choice
from zope.schema import Date
from zope.schema import TextLine
from zope.schema import ValidationError

import six


class InvalidDate(ValidationError):
    __doc__ = _("invalid_date")


class InvalidTime(ValidationError):
    __doc__ = _("invalid_time")


def check_time(value):
    """
    If value exist it should match TELEPHONE_PATTERN
    """
    if not value:
        return True
    if isinstance(value, six.string_types):
        value = value.strip()
    try:
        hh, mm = list(map(int, value.split(":")))
        assert 0 <= hh <= 23
        assert 0 <= mm <= 59
        return True
    except Exception:
        msg = "Invalid time: %r" % value
        logger.exception(msg)
    raise InvalidTime(value)


class IVacationBooking(Interface):
    title = TextLine(
        title=_("label_title", u"Title"),
        description=_(
            "description_title", u"This text will appear in the calendar cells"
        ),
        default=u"",
    )
    gate = Choice(
        title=_("label_gate", u"Gate"),
        description=_(
            "description_gate", u"The gate that will be unavailable"
        ),
        default=u"",
        vocabulary="redturtle.prenotazioni.gates",
    )
    start_date = Date(
        title=_("label_start", u"Start date "),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
    )
    start_time = TextLine(
        title=_("label_start_time", u"Start time"),
        description=_("invalid_time"),
        constraint=check_time,
        default=u"00:00",
    )
    end_time = TextLine(
        title=_("label_end_time", u"End time"),
        description=_("invalid_time"),
        constraint=check_time,
        default=u"23:59",
    )


@implementer(IVacationBooking)
class VacationBooking(form.Form):

    """
    This is a view that allows to book a gate for a certain period
    """

    ignoreContext = True

    @property
    def fields(self):
        fields = field.Fields(IVacationBooking)
        if not self.context.getGates():
            return fields.omit("gate")
        return fields

    def updateWidgets(self):
        super(VacationBooking, self).updateWidgets()
        self.widgets["start_date"].value = datetime.today().strftime(
            "%Y-%m-%d"
        )

    def get_parsed_data(self, data):
        """
        Return the data already parsed for our convenience
        """
        parsed_data = data.copy()
        parsed_data["start_date"] = data["start_date"]  # noqa
        parsed_data["start_time"] = time2timedelta(data["start_time"])
        parsed_data["end_time"] = time2timedelta(data["end_time"])
        return parsed_data

    @property
    @memoize
    def prenotazioni(self):
        """
        The prenotazioni_context_state view in the context
        """
        return api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )

    def get_start_time(self, data):
        """ The requested start time

        :returns: a datetime
        """
        return (
            datetime(*data["start_date"].timetuple()[:6]) + data["start_time"]
        )  # noqa

    def get_end_time(self, data):
        """ The requested end time

        :returns: a datetime
        """
        return datetime(*data["start_date"].timetuple()[:6]) + data["end_time"]

    def get_vacation_slot(self, data):
        """ The requested vacation slot
        """
        start_time = self.get_start_time(data)
        end_time = self.get_end_time(data)
        return BaseSlot(start_time, end_time)

    def get_slots(self, data):
        """
        Get the slots we want to book!
        """
        start_date = data["start_date"]
        gate = data.get("gate", "")
        vacation_slot = self.get_vacation_slot(data)
        slots = []
        for period in ("morning", "afternoon"):
            free_slots = self.prenotazioni.get_free_slots(start_date, period)
            gate_free_slots = free_slots.get(gate, [])
            [
                slots.append(vacation_slot.intersect(slot))
                for slot in gate_free_slots
                if vacation_slot.overlaps(slot)
            ]
        return slots

    # def set_invariant_error(self, errors, fields, msg):
    #     '''
    #     Set an error with invariant validation to highlights the involved
    #     fields
    #     '''
    #     for field in fields:
    #         label = self.widgets[field].label
    #         error = WidgetInputError(field, label, msg)
    #         errors.append(error)
    #         self.widgets[field].error = msg

    def has_slot_conflicts(self, data):
        """ We want the operator to handle conflicts:
        no other booking can be created if we already have stuff
        """
        start_date = data["start_date"]
        busy_slots = self.prenotazioni.get_busy_slots(start_date)
        if not busy_slots:
            return False
        gate_busy_slots = busy_slots.get(data.get("gate", ""), [])
        if not gate_busy_slots:
            return False
        vacation_slot = self.get_vacation_slot(data)
        for slot in gate_busy_slots:
            if vacation_slot.intersect(slot):
                return True
        return False

    # def validate_invariants(self, data, errors):
    #     ''' Validate invariants errors
    #     '''
    #     parsed_data = self.get_parsed_data(data)
    #     start_date = data['start_date']
    #     if self.has_slot_conflicts(parsed_data):
    #         msg = _('slot_conflict_error',
    #                 u'This gate has some booking schedule in this time '
    #                 u'period.')
    #     elif not self.prenotazioni.is_valid_day(start_date):
    #         msg = _('day_error',
    #                 u'This day is not valid.')
    #     else:
    #         msg = ''
    #     if not msg:
    #         return
    #     fields_to_notify = ['start_date', 'start_time', 'end_time']
    #     self.set_invariant_error(errors, fields_to_notify, msg)

    # def validate(self, action, data):
    #     '''
    #     Checks if we can book those data
    #     '''
    #     errors = super(VacationBooking, self).validate(action, data)
    #     self.validate_invariants(data, errors)
    #     if not 'gate' in data:
    #         data['gate'] = u''
    #     return errors

    def do_book(self, data):
        """
        Execute the multiple booking
        """
        booker = IBooker(self.context.aq_inner)
        slots = self.get_slots(data)
        start_date = DateTime(data["start_date"].strftime("%Y/%m/%d"))
        for slot in slots:
            booking_date = start_date + (float(slot.lower_value) / 86400)
            slot.__class__ = BaseSlot
            duration = float(len(slot)) / 86400
            # duration = float(len(slot)) / 60
            slot_data = {
                "fullname": data.get("title", u""),
                "subject": u"",
                "agency": u"",
                "booking_date": booking_date,
                "phone": u"",
                "email": u"",
                "tipologia_prenotazione": u"",
            }
            booker.create(
                slot_data, duration=duration, force_gate=data.get("gate")
            )

        msg = _("booking_created")
        IStatusMessage(self.request).add(msg, "info")

    @button.buttonAndHandler(_(u"action_book", default=u"Book"))
    def action_book(self, action):
        """
        Book this resource
        """
        data, errors = self.extractData()
        parsed_data = self.get_parsed_data(data)

        start_date = data["start_date"]
        if self.has_slot_conflicts(parsed_data):
            msg = _(
                "slot_conflict_error",
                u"This gate has some booking schedule in this time "
                u"period.",
            )
            raise ActionExecutionError(Invalid(msg))

        elif not self.prenotazioni.is_valid_day(start_date):
            msg = _("day_error", u"This day is not valid.")
            raise ActionExecutionError(Invalid(msg))

        self.do_book(parsed_data)
        qs = {"data": data["start_date"].strftime("%d/%m/%Y")}
        target = urlify(self.context.absolute_url(), params=qs)
        return self.request.response.redirect(target)

    @button.buttonAndHandler(_(u"action_cancel", default=u"Cancel"))
    def action_cancel(self, action):
        """
        Cancel
        """
        target = self.context.absolute_url()
        return self.request.response.redirect(target)

    def extra_script(self):
        """ The scripts needed for the dateinput
        """
        view = api.content.get_view(
            "redturtle.prenotazioni.dateinput.conf.js",
            self.context,
            self.request,
        )
        return view.render() + view.mark_with_class(["#form\\\\.start_date"])


class VacationBookingShow(BrowserView):

    """
    Should this functionality be published?
    """

    def __call__(self):
        """ Return True for the time being
        """
        return True

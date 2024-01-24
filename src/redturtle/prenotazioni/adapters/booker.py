# -*- coding: utf-8 -*-
import math
from datetime import timedelta
from random import choice

from DateTime import DateTime
from plone import api
from plone.memoize.instance import memoize
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.parse import urlparse
from zope.annotation.interfaces import IAnnotations
from zope.component import Interface
from zope.component import getMultiAdapter
from zope.event import notify
from zope.interface import implementer
from ZTUtils.Lazy import LazyMap

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.adapters.booking_code import IBookingCodeGenerator
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.behaviors.booking_folder.notifications.email.events import (
    booking_folder_provides_current_behavior as booking_folder_provides_email_notification_behavior,
)
from redturtle.prenotazioni.config import VERIFIED_BOOKING
from redturtle.prenotazioni.content.prenotazione import VACATION_TYPE
from redturtle.prenotazioni.exceptions import BookerException
from redturtle.prenotazioni.exceptions import BookingsLimitExceded
from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.prenotazione_event import MovedPrenotazione
from redturtle.prenotazioni.utilities.dateutils import exceedes_date_limit


class IBooker(Interface):
    """Interface for a booker"""


@implementer(IBooker)
class Booker(object):
    portal_type = "Prenotazione"

    def __init__(self, context):
        """
        @param context: a PrenotazioniFolder object
        """
        self.context = context

    @property
    @memoize
    def prenotazioni(self):
        """The prenotazioni context state view"""
        return self.context.unrestrictedTraverse("@@prenotazioni_context_state")  # noqa

    def _validate_user_limit(self, data: dict):
        """Control if user did not exceed the limit yet

        Args:
            data (dict): booking data

        Returns:
          None

        Raises:
            BookingsLimitExceded: User exceeded limit
        """

        if not self.context.max_bookings_allowed:
            return
        if data.get("booking_type", "") == "out-of-office":
            # don't limit number of out-of-office
            return
        if len(
            self.search_future_bookings_by_fiscalcode(
                data["fiscalcode"], data["booking_type"]
            )
        ) >= (self.context.max_bookings_allowed):
            raise BookingsLimitExceded(self.context, booking_type=data["booking_type"])

    @property
    def is_manager(self):
        """
        Check if current user is Gestore
        """
        return api.user.has_permission(
            "redturtle.prenotazioni: Manage Prenotazioni", obj=self.context
        )

    def search_future_bookings_by_fiscalcode(
        self, fiscalcode: str, booking_type: str = None
    ) -> LazyMap:
        """Find all the future bookings registered for the same fiscalcode"""
        query = dict(
            portal_type="Prenotazione",
            fiscalcode=fiscalcode,
            path={"query": "/".join(self.context.getPhysicalPath())},
            Date={"query": DateTime(), "range": "min"},
            review_state={
                "query": ("confirmed", "pending", "private"),
            },
        )

        if booking_type:
            query["booking_type"] = booking_type

        return api.portal.get_tool("portal_catalog").unrestrictedSearchResults(**query)

    def get_available_gate(self, booking_date, booking_expiration_date=None):
        """
        Find which gate are free to serve this booking and choose randomly
        one of the less busy
        """
        # XXX: per come è ora la funzione probabilmente questa condizione non è mai vera
        # if not self.prenotazioni.get_gates():
        #     return ""
        available_gates = self.prenotazioni.get_free_gates_in_slot(
            booking_date, booking_expiration_date
        )
        if len(available_gates) == 0:
            return None
        return choice(list(available_gates))

        # if len(available_gates) == 1:
        #    return available_gates[0]
        # this was code to choose a less used gate that we temporary disabled
        # free_slots_by_gate = self.prenotazioni.get_free_slots(booking_date)
        # # Create a dictionary where keys is the time the gate is free, and
        # # value is a list of gates
        # free_time_map = {}
        # for gate, free_slots in free_slots_by_gate.items():
        #     if gate not in available_gates:
        #         # this gate have already a booking for selected time, skip it
        #         continue
        #     free_time = sum(map(BaseSlot.__len__, free_slots))
        #     free_time_map.setdefault(free_time, []).append(gate)
        # # Get a random choice among the less busy ones
        # max_free_time = max(free_time_map.keys())
        # less_used_gates = free_time_map[max_free_time]
        # return choice(less_used_gates)

    def check_future_days(self, booking, data):
        """
        Check if date is in the right range.
        Managers bypass this check
        """
        future_days = booking.getFutureDays()
        if future_days and not self.prenotazioni.user_can_manage_prenotazioni:
            if exceedes_date_limit(data, future_days):
                msg = _("Sorry, you can not book this slot for now.")
                raise BookerException(api.portal.translate(msg))

    def generate_params(self, data, force_gate, duration):
        # remove empty fields
        params = {k: v for k, v in data.items() if v}
        booking_type = params.get("booking_type", "")
        user = api.user.get_current()

        # set expiration date
        if duration < 0:
            # if we pass a negative duration it will be recalculated
            duration = self.prenotazioni.get_booking_type_duration(booking_type)
            # duration = (float(duration) / MIN_IN_DAY)
            params["booking_expiration_date"] = params["booking_date"] + timedelta(
                minutes=duration
            )
        else:
            params["booking_expiration_date"] = params["booking_date"] + timedelta(
                minutes=duration
            )

        # set gate
        gate = ""
        if force_gate:
            gate = force_gate
        else:
            available_gate = self.get_available_gate(
                params["booking_date"], params["booking_expiration_date"]
            )
            if available_gate:
                gate = available_gate
        params["gate"] = gate

        # set fiscal code
        fiscalcode = data.get("fiscalcode", "")

        if not fiscalcode:
            fiscalcode = user.getProperty("fiscalcode", "") or user.getId() or ""

        if fiscalcode:
            params["fiscalcode"] = fiscalcode.upper()

        return params

    def _create(self, data, duration=-1, force_gate=""):
        """Create a Booking object

        :param duration: used to force a duration. If it is negative it will be
                         calculated using the booking_type
        :param force_gate: by default gates are assigned randomly except if you
                           pass this parameter.
        """
        params = self.generate_params(
            data=data, duration=duration, force_gate=force_gate
        )
        if not params.get("gate", ""):
            # no gate available
            return

        self._validate_user_limit(params)
        container = self.prenotazioni.get_container(
            params["booking_date"], create_missing=True
        )

        booking = api.content.create(
            type="Prenotazione",
            container=container,
            **params,
        )

        # set booking_code
        booking_code = getMultiAdapter(
            (booking, self.context.REQUEST), IBookingCodeGenerator
        )()
        setattr(booking, "booking_code", booking_code)

        # check verified booking
        user = api.user.get_current()
        annotations = IAnnotations(booking)
        annotations[VERIFIED_BOOKING] = False
        if not api.user.is_anonymous() and not api.user.has_permission(
            "Modify portal content", obj=container
        ):
            fiscalcode = params.get("fiscalcode", "")
            if user.hasProperty("fiscalcode") and fiscalcode:
                if (user.getProperty("fiscalcode") or "").upper() == fiscalcode:
                    logger.info("Booking verified: {}".format(booking.absolute_url()))
                    annotations[VERIFIED_BOOKING] = True

        booking.reindexObject()
        api.content.transition(booking, "submit")

        # finally send email notification to managers
        self.send_email_to_managers(booking=booking)

        return booking

    def send_email_to_managers(self, booking):
        """
        Send email notification for managers
        """
        if not booking_folder_provides_email_notification_behavior(booking):
            return

        if booking.isVacation():
            return
        if not getattr(booking, "email_responsabile", []):
            return
        request = self.context.REQUEST
        message_adapter = getMultiAdapter(
            (booking, request),
            IBookingEmailMessage,
            name="notify_manager",
        )
        sender_adapter = getMultiAdapter(
            (message_adapter, booking, request),
            IBookingNotificationSender,
            name="booking_transition_email_sender",
        )

        sender_adapter.send(force=True)

    def fix_container(self, booking):
        """Take a booking and move it to the right date"""
        booking_date = booking.getBooking_date()
        old_container = booking.aq_parent
        new_container = self.prenotazioni.get_container(
            booking_date, create_missing=True
        )
        if old_container == new_container:
            booking.reindexObject(idxs=["Date"])
            return
        api.content.move(booking, new_container)

    def book(self, data, force_gate=None, duration=-1):
        """
        Create a Booking object

        Like create but we disable security checks to allow creation
        for anonymous users
        """
        data["booking_date"] = datetime_with_tz(data["booking_date"])

        self.check_future_days(booking=self.context, data=data)

        conflict_manager = self.prenotazioni.conflict_manager
        if conflict_manager.conflicts(data):
            msg = _("Sorry, this slot is not available anymore.")
            raise BookerException(api.portal.translate(msg))

        # XXX: deprecated
        referer = self.context.REQUEST.get("HTTP_REFERER", None)
        if referer:
            parsed_url = urlparse(referer)
            params = parse_qs(parsed_url.query)
            if "gate" in params:
                force_gate = params["gate"][0]

        with api.env.adopt_roles(["Manager", "Member"]):
            obj = self._create(data, duration=duration, force_gate=force_gate)

        if not obj:
            msg = _("Sorry, this slot is not available anymore.")
            raise BookerException(api.portal.translate(msg))

        if self.is_manager:
            if not getattr(self.context, "auto_confirm", False) and getattr(
                self.context, "auto_confirm_manager", False
            ):
                if api.content.get_state(obj) != "confirmed":
                    api.content.transition(obj, transition="confirm")
        return obj

    def move(self, booking, data):
        """
        Move a booking in a new slot
        """
        data["booking_date"] = booking_date = datetime_with_tz(data["booking_date"])

        data["booking_type"] = booking.getBooking_type()
        conflict_manager = self.prenotazioni.conflict_manager
        current_data = booking.getBooking_date()
        current = {
            "booking_date": current_data,
            "booking_type": data["booking_type"],
        }
        current_slot = conflict_manager.get_choosen_slot(current)
        current_gate = getattr(booking, "gate", "")
        exclude = {current_gate: [current_slot]}
        if conflict_manager.conflicts(data, exclude=exclude):
            msg = _(
                "Sorry, this slot is not available or does not fit your " "booking."
            )
            raise BookerException(api.portal.translate(msg))

        self.check_future_days(booking=booking, data=data)

        # move the booking
        duration = booking.getDuration()
        booking_expiration_date = booking_date + duration
        booking.setBooking_date(booking_date)
        booking.setBooking_expiration_date(booking_expiration_date)

        # se non passato il gate va bene lasciare quello precedente o
        # va rimosso ?
        if data.get("gate"):
            booking.gate = data["gate"]

        booking.reindexObject(idxs=["Subject"])
        notify(MovedPrenotazione(booking))

    def create_vacation(self, data):
        data["start"] = start = datetime_with_tz(data["start"])
        data["end"] = end = datetime_with_tz(data["end"])
        gate = data.get("gate", "")

        has_slot_conflicts = False
        # XXX: questa funzione prende uno date o un datetime ?
        busy_slots = self.prenotazioni.get_busy_slots(start)
        vacation_slot = BaseSlot(start, end)
        if busy_slots:
            gate_busy_slots = busy_slots.get(gate, [])
            if gate_busy_slots:
                for slot in gate_busy_slots:
                    intersection = vacation_slot.intersect(slot)
                    if (
                        intersection
                        and intersection.lower_value != intersection.upper_value
                    ):
                        has_slot_conflicts = True
                        break

        if has_slot_conflicts:
            msg = api.portal.translate(
                _("This gate has some booking schedule in this time period.")
            )
            raise BookerException(msg)

        if not self.prenotazioni.is_valid_day(start.date()):
            msg = self.context.translate(_("This day is not valid."))
            raise BookerException(msg)

        for period in ("morning", "afternoon"):
            free_slots = self.prenotazioni.get_free_slots(start, period)
            gate_free_slots = free_slots.get(gate, [])
            for slot in gate_free_slots:
                if vacation_slot.overlaps(slot):
                    # there is a slot that overlaps with the vacation
                    duration = math.ceil((end - start).seconds / 60)
                    # XXX: weird to remove the gate from data and then force it ...
                    slot_data = {k: v for k, v in data.items() if k != "gate"}
                    slot_data["booking_date"] = start
                    slot_data["booking_type"] = VACATION_TYPE
                    if self.book(slot_data, duration=duration, force_gate=gate):
                        return 1

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
from zope.event import notify
from zope.interface import implementer
from ZTUtils.Lazy import LazyMap

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.config import VERIFIED_BOOKING
from redturtle.prenotazioni.content.prenotazione import VACATION_TYPE
from redturtle.prenotazioni.exceptions import BookerException
from redturtle.prenotazioni.exceptions import BookingsLimitExceded
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
        Find which gate is free to serve this booking
        """
        # XXX: per come è ora la funzione probabilmente questa condizione non è mai vera
        # if not self.prenotazioni.get_gates():
        #     return ""
        available_gates = self.prenotazioni.get_free_gates_in_slot(
            booking_date, booking_expiration_date
        )
        if len(available_gates) == 0:
            return None
        if len(available_gates) == 1:
            return available_gates.pop()
        return choice(self.prenotazioni.get_less_used_gates(booking_date))

    def _create(self, data, duration=-1, force_gate=""):
        """Create a Booking object

        :param duration: used to force a duration. If it is negative it will be
                         calculated using the booking_type
        :param force_gate: by default gates are assigned randomly except if you
                           pass this parameter.
        """
        # remove empty fields
        params = {k: v for k, v in data.items() if v}

        container = self.prenotazioni.get_container(
            params["booking_date"], create_missing=True
        )
        booking_type = params.get("booking_type", "")
        if duration < 0:
            # if we pass a negative duration it will be recalculated
            duration = self.prenotazioni.get_booking_type_duration(booking_type)
            # duration = (float(duration) / MIN_IN_DAY)
            booking_expiration_date = params["booking_date"] + timedelta(
                minutes=duration
            )
        else:
            booking_expiration_date = params["booking_date"] + timedelta(
                minutes=duration
            )

        gate = ""
        if not force_gate:
            available_gate = self.get_available_gate(
                params["booking_date"], booking_expiration_date
            )
            # if not available_gate: #
            if available_gate is None:
                # there isn't a free slot in any available gates
                return None
            # else assign the gate to the booking
            gate = available_gate
        else:
            gate = force_gate

        fiscalcode = data.get("fiscalcode", "") or ""
        fiscalcode.upper()
        user = api.user.get_current()

        if not fiscalcode:
            fiscalcode = (
                user.getProperty("fiscalcode", "") or user.getId() or ""
            ).upper()  # noqa

        if fiscalcode:
            params["fiscalcode"] = fiscalcode
            self._validate_user_limit(params)

        obj = api.content.create(
            type="Prenotazione",
            container=container,
            booking_expiration_date=booking_expiration_date,
            gate=gate,
            **params,
        )

        annotations = IAnnotations(obj)

        annotations[VERIFIED_BOOKING] = False

        if not api.user.is_anonymous() and not api.user.has_permission(
            "Modify portal content", obj=container
        ):
            if user.hasProperty("fiscalcode") and fiscalcode:
                if (user.getProperty("fiscalcode") or "").upper() == fiscalcode:
                    logger.info("Booking verified: {}".format(obj.absolute_url()))
                    annotations[VERIFIED_BOOKING] = True

        obj.reindexObject()
        api.content.transition(obj, "submit")
        return obj

    def create(self, data, duration=-1, force_gate=""):
        """
        Create a Booking object

        Like create but we disable security checks to allow creation
        for anonymous users
        """
        with api.env.adopt_roles(["Manager", "Member"]):
            return self._create(data, duration=duration, force_gate=force_gate)

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
        Book a resource
        """
        data["booking_date"] = datetime_with_tz(data["booking_date"])

        conflict_manager = self.prenotazioni.conflict_manager
        if conflict_manager.conflicts(data):
            msg = _("Sorry, this slot is not available anymore.")
            raise BookerException(api.portal.translate(msg))

        future_days = self.context.getFutureDays()
        if future_days and exceedes_date_limit(data, future_days):
            msg = _("Sorry, you can not book this slot for now.")
            raise BookerException(api.portal.translate(msg))

        # XXX: deprecated
        referer = self.context.REQUEST.get("HTTP_REFERER", None)
        if referer:
            parsed_url = urlparse(referer)
            params = parse_qs(parsed_url.query)
            if "gate" in params:
                force_gate = params["gate"][0]

        obj = self.create(data=data, force_gate=force_gate, duration=duration)
        if not obj:
            msg = _("Sorry, this slot is not available anymore.")
            raise BookerException(api.portal.translate(msg))
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

        future_days = booking.getFutureDays()
        if future_days and exceedes_date_limit(data, future_days):
            msg = _("Sorry, you can not book this slot for now.")
            raise BookerException(api.portal.translate(msg))

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
                    if self.create(slot_data, duration=duration, force_gate=gate):
                        return 1

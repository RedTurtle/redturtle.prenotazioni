# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import time
from datetime import timedelta
from DateTime import DateTime
from plone import api
from plone.memoize.instance import memoize
from random import choice
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.adapters.prenotazione import IDeleteTokenProvider
from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from redturtle.prenotazioni.config import VERIFIED_BOOKING
from zope.annotation.interfaces import IAnnotations
from zope.component import Interface
from zope.interface import implementer


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

    def get_available_gate(self, booking_date, booking_expiration_date=None):
        """
        Find which gate is free to serve this booking
        """
        if not self.prenotazioni.get_gates():
            return ""
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
        if isinstance(params["booking_date"], DateTime):
            params["booking_date"] = params["booking_date"].asdatetime()
        else:
            params["booking_date"] = params["booking_date"]

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
            # in this case we need to deal with seconds converted in days
            booking_expiration_date = params["booking_date"] + timedelta(days=duration)

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
        obj = api.content.create(
            type="Prenotazione",
            container=container,
            booking_expiration_date=booking_expiration_date,
            gate=gate,
            **params
        )

        # set delete token
        expiration = datetime.combine(obj.booking_date.date(), time(0, 0, 0))
        token = IDeleteTokenProvider(obj).generate_token(expiration=expiration)
        annotations = IAnnotations(obj)
        annotations[DELETE_TOKEN_KEY] = token.decode("utf-8")

        annotations[VERIFIED_BOOKING] = False
        if not api.user.is_anonymous():
            user = api.user.get_current()
            data_fiscalcode = getattr(obj, "fiscalcode", "") or ""
            fiscalcode = data_fiscalcode.upper()
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

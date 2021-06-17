# -*- coding: utf-8 -*-
from datetime import timedelta
from DateTime import DateTime
from plone import api
from plone.memoize.instance import memoize
from random import choice
from zope.component import Interface
from zope.interface import implementer
from redturtle.prenotazioni.adapters.prenotazione import IDeleteTokenProvider
from zope.annotation.interfaces import IAnnotations
from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from datetime import datetime, time


class IBooker(Interface):
    """ Interface for a booker
    """


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
        """ The prenotazioni context state view
        """
        return self.context.unrestrictedTraverse(
            "@@prenotazioni_context_state"
        )  # noqa

    def get_available_gate(self, data_prenotazione, data_scadenza=None):
        """
        Find which gate is free to serve this booking
        """
        if not self.prenotazioni.get_gates():
            return ""
        available_gates = self.prenotazioni.get_free_gates_in_slot(
            data_prenotazione, data_scadenza
        )
        if len(available_gates) == 0:
            return None
        if len(available_gates) == 1:
            return available_gates.pop()
        return choice(self.prenotazioni.get_less_used_gates(data_prenotazione))

    def _create(self, data, duration=-1, force_gate=""):
        """ Create a Booking object

        :param duration: used to force a duration. If it is negative it will be
                         calculated using the tipology
        :param force_gate: by default gates are assigned randomly except if you
                           pass this parameter.
        """
        if isinstance(data["booking_date"], DateTime):
            booking_date = data["booking_date"].asdatetime()
        else:
            booking_date = data["booking_date"]

        container = self.prenotazioni.get_container(
            booking_date, create_missing=True
        )
        tipology = data.get("tipology", "")
        if duration < 0:
            # if we pass a negative duration it will be recalculated
            duration = self.prenotazioni.get_tipology_duration(tipology)
            # duration = (float(duration) / MIN_IN_DAY)
            data_scadenza = booking_date + timedelta(minutes=duration)
        else:
            # in this case we need to deal with seconds converted in days
            data_scadenza = booking_date + timedelta(days=duration)

        at_data = {
            "title": data["fullname"],
            "description": data["subject"] or "",
            "azienda": data.get("agency", ""),
            "fiscalcode": data.get("fiscalcode", ""),
            "data_prenotazione": booking_date,
            "data_scadenza": data_scadenza,
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "tipologia_prenotazione": data.get("tipology", ""),
        }
        if not force_gate:
            available_gate = self.get_available_gate(
                booking_date, data_scadenza
            )
            # if not available_gate: #
            if available_gate is None:
                # there isn't a free slot in any available gates
                return None
            # else assign the gate to the booking
            at_data["gate"] = available_gate
        else:
            at_data["gate"] = force_gate

        obj = api.content.create(
            type="Prenotazione", title=at_data["title"], container=container
        )

        for attribute in at_data.keys():
            setattr(obj, attribute, at_data[attribute])

        # set delete token
        expiration = datetime.combine(
            obj.data_prenotazione.date(), time(0, 0, 0)
        )
        token = IDeleteTokenProvider(obj).generate_token(expiration=expiration)
        annotations = IAnnotations(obj)
        annotations[DELETE_TOKEN_KEY] = token.decode("utf-8")

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
        """ Take a booking and move it to the right date
        """
        booking_date = booking.getData_prenotazione()
        old_container = booking.aq_parent
        new_container = self.prenotazioni.get_container(
            booking_date, create_missing=True
        )
        if old_container == new_container:
            booking.reindexObject(idxs=["Date"])
            return
        api.content.move(booking, new_container)

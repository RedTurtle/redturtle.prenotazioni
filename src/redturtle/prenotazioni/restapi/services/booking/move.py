# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.prenotazione_event import MovedPrenotazione

# from redturtle.prenotazioni.utilities.dateutils import as_naive_utc
from zope.event import notify
from zope.interface import alsoProvides


class MoveBooking(Service):
    def exceedes_date_limit(self, booking, data):
        """
        Check if we can book this slot or is it too much in the future.
        """
        future_days = booking.getFutureDays()
        if not future_days:
            return False
        booking_date = data.get("booking_date", None)
        if not isinstance(booking_date, datetime):
            return False
        date_limit = tznow() + timedelta(future_days)
        if booking_date <= date_limit:
            return False
        return True

    def reply(self):
        """
        @param booking_id
        @param booking_date
        @param gate (optional) -- se non definito alla move viene assegnato
                                  il gate di default (?)
        @return: 201 OK

        see: src/redturtle/prenotazioni/browser/prenotazione_move.py
        """
        data = json_body(self.request)
        booking_id = data.get("booking_id", None)

        data["booking_date"] = booking_date = datetime.fromisoformat(
            data["booking_date"]
        )

        booking = api.content.get(UID=booking_id)
        # booking.moveBooking(booking_date)

        prenotazioni_view = api.content.get_view(
            "prenotazioni_context_state",
            self.context,
            self.request,
        )

        # data, errors = self.extractData()
        data["booking_type"] = booking.getBooking_type()
        conflict_manager = prenotazioni_view.conflict_manager
        current = {
            "booking_date": booking.getBooking_date(),
            "booking_type": data["booking_type"],
        }
        current_slot = conflict_manager.get_choosen_slot(current)
        current_gate = getattr(booking, "gate", "")
        exclude = {current_gate: [current_slot]}
        if conflict_manager.conflicts(data, exclude=exclude):
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("Sorry, this slot is not available or does not fit your booking.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        if self.exceedes_date_limit(booking, data):
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("Sorry, you can not book this slot for now.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        # self.do_move(data)
        # booking_date = data["booking_date"]
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

        # msg = _("booking_moved")
        # IStatusMessage(self.request).add(msg, "info")
        # booking_date = data["booking_date"].strftime("%d/%m/%Y")
        # target = urlify(
        #     self.prenotazioni_folder.absolute_url(),
        #     paths=["prenotazioni_week_view"],
        #     params={"data": booking_date},
        # )

        alsoProvides(self.request, IDisableCSRFProtection)
        # TODO: valutare se serve tornare del contenuto
        self.request.response.setStatus(201)
        return

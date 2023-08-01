# -*- coding: utf-8 -*-
from plone.restapi.services import Service
from plone.restapi.deserializer import json_body
from plone import api
from redturtle.prenotazioni.adapters.slot import BaseSlot
from datetime import datetime
from redturtle.prenotazioni.adapters.booker import IBooker
from DateTime import DateTime
from redturtle.prenotazioni import _
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides
from redturtle.prenotazioni.dateutils import as_naive_utc


class AddVacation(Service):
    #       class=".vacations.VacationBooking"

    def reply(self):
        data = json_body(self.request)
        start = as_naive_utc(datetime.fromisoformat(data["start"]))
        end = as_naive_utc(datetime.fromisoformat(data["end"]))
        gate = data.get("gate")
        # title = data.get("title")

        prenotazioni_context_state = api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )

        has_slot_conflicts = False
        # XXX: questa funzione prende uno date o un datetime ?
        busy_slots = prenotazioni_context_state.get_busy_slots(start)
        vacation_slot = BaseSlot(start, end)
        if busy_slots:
            gate_busy_slots = busy_slots.get(gate, [])
            if gate_busy_slots:
                for slot in gate_busy_slots:
                    if vacation_slot.intersect(slot):
                        has_slot_conflicts = True
                        break

        if has_slot_conflicts:
            self.request.response.setStatus(400)
            msg = self.context.translate(
                _("This gate has some booking schedule in this time period.")
            )
            return dict(error=dict(type="Bad Request", message=msg))

        if not prenotazioni_context_state.is_valid_day(start.date()):
            self.request.response.setStatus(400)
            msg = self.context.translate(_("This day is not valid."))
            return dict(error=dict(type="Bad Request", message=msg))

        # self.do_book(parsed_data)
        # slots = self.get_slots(data)
        slots = []
        for period in ("morning", "afternoon"):
            free_slots = prenotazioni_context_state.get_free_slots(start, period)
            gate_free_slots = free_slots.get(gate, [])
            [
                slots.append(vacation_slot.intersect(slot))
                for slot in gate_free_slots
                if vacation_slot.overlaps(slot)
            ]

        alsoProvides(self.request, IDisableCSRFProtection)
        booker = IBooker(self.context.aq_inner)
        # XXX: quest conto di giorni è corretto ? non è mica chiaro cosa fa ...
        #      ... anche il gioco di valorizzare __class__ mi pare abbastanza
        #      bizzarro
        start_date = DateTime(start.strftime("%Y/%m/%d"))
        for slot in slots:
            booking_date = start_date + (float(slot.lower_value) / 86400)
            slot.__class__ = BaseSlot
            duration = float(len(slot)) / 86400
            # duration = float(len(slot)) / 60
            slot_data = {k: v for k, v in data.items() if k != "gate"}
            slot_data["booking_date"] = booking_date
            booker.create(slot_data, duration=duration, force_gate=gate)

        self.request.response.setStatus(201)

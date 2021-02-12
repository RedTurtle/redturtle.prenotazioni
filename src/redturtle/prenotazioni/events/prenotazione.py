# -*- coding: utf-8 -*-
from redturtle.prenotazioni.adapters.booker import IBooker
import logging

logger = logging.getLogger(__name__)


def reallocate_gate(obj):
    """
    We have to reallocate the gate for this object

    Skip this step if we have a form.gate parameter in the request

    DISABLED: SEEMS ONLY GENERATES PROBLEMS
    """
    context = obj.object

    if context.REQUEST.form.get("form.gate", "") and getattr(
        context, "gate", ""
    ):
        return

    container = context.getPrenotazioniFolder()
    booking_date = context.getData_prenotazione()
    new_gate = IBooker(container).get_available_gate(booking_date)
    if new_gate:
        context.gate = new_gate


def reallocate_container(obj):
    """
    If we moved Prenotazione to a new week we should move it
    """
    container = obj.object.getPrenotazioniFolder()
    IBooker(container).fix_container(obj.object)

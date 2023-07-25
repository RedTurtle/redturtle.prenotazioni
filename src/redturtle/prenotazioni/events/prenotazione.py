# -*- coding: utf-8 -*-
from Acquisition import aq_chain
from zope.component import getMultiAdapter
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from plone import api

from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.adapters.booker import IBooker


def get_prenotazione_folder(prenotazione):
    return [
        i
        for i in aq_chain(prenotazione)
        if getattr(i, "portal_type", "") == "PrenotazioniFolder"
    ][0]


def reallocate_gate(obj):
    """
    We have to reallocate the gate for this object

    Skip this step if we have a form.gate parameter in the request

    DISABLED: SEEMS ONLY GENERATES PROBLEMS
    """
    context = obj.object

    if context.REQUEST.form.get("form.gate", "") and getattr(context, "gate", ""):
        return

    container = context.getPrenotazioniFolder()
    booking_date = context.getBooking_date()
    new_gate = IBooker(container).get_available_gate(booking_date)
    if new_gate:
        context.gate = new_gate


def reallocate_container(obj):
    """
    If we moved Prenotazione to a new week we should move it
    """
    container = obj.object.getPrenotazioniFolder()
    IBooker(container).fix_container(obj.object)


def notify_on_after_transition_event(context, event):
    """The messages are being send only if the following flags on the PrenotazioniFolder are set"""

    flags = {
        i: getattr(get_prenotazione_folder(context), f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }
    if flags["confirm"] and flags["submit"]:
        flags["submit"] = False

    if flags.get(event.transition and event.transition.__name__ or "", False):
        adapter = getMultiAdapter(
            (context, event),
            IPrenotazioneEmailMessage,
            name=event.transition.__name__,
        )

        if adapter:
            if adapter.message:
                send_email(adapter.message)


def autoconfirm(context, event):
    if api.content.get_state(obj=context, default=None) == "pending":
        if getattr(get_prenotazione_folder(context), "auto_confirm", False):
            api.content.transition(obj=context, transition="confirm")


def notify_on_move(context, event):
    if getattr(get_prenotazione_folder(context), "notify_on_move", False):
        adapter = getMultiAdapter((context, event), IPrenotazioneEmailMessage)
        if adapter:
            if adapter.message:
                send_email(adapter.message)


def send_email(msg):
    host = api.portal.get_tool(name="MailHost")
    registry = getUtility(IRegistry)
    encoding = registry.get("plone.email_charset", "utf-8")

    host.send(msg, charset=encoding)

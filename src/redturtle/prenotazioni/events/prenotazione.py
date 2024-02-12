# -*- coding: utf-8 -*-
from email.utils import formataddr
from email.utils import parseaddr

from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zope.component import getUtility

from redturtle.prenotazioni.adapters.booker import IBooker


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
    with api.env.adopt_roles(["Manager"]):
        IBooker(container).fix_container(obj.object)


def autoconfirm(booking, event):
    if api.content.get_state(obj=booking, default=None) == "pending":
        if getattr(booking.getPrenotazioniFolder(), "auto_confirm", False):
            api.content.transition(obj=booking, transition="confirm")
            booking.reindexObject(idxs="review_state")


def get_mail_from_address():
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix="plone", check=False)
    from_address = mail_settings.email_from_address
    from_name = mail_settings.email_from_name

    if not from_address:
        return ""
    from_address = from_address.strip()
    mfrom = formataddr((from_name, from_address))
    if parseaddr(mfrom)[1] != from_address:
        mfrom = from_address
    return mfrom

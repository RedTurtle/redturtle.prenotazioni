# -*- coding: utf-8 -*-
import hashlib
from email.utils import formataddr
from email.utils import parseaddr
from logging import getLogger

from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zope.component import getMultiAdapter
from zope.component import getUtility

from redturtle.prenotazioni import is_migration
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage

logger = getLogger(__name__)


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
    if is_migration():
        return
    booking_folder = context.getPrenotazioniFolder()
    flags = {
        i: getattr(booking_folder, f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }

    if flags["confirm"] and getattr(booking_folder, "auto_confirm", False):
        flags["submit"] = False

    if flags.get(event.transition and event.transition.__name__ or "", False):
        if not getattr(context, "email", ""):
            # booking does not have an email set
            return
        adapter = getMultiAdapter(
            (context, event),
            IPrenotazioneEmailMessage,
            name=event.transition.__name__,
        )

        if adapter:
            if adapter.message:
                send_email(adapter.message)


def autoconfirm(booking, event):
    if api.content.get_state(obj=booking, default=None) == "pending":
        if getattr(booking.getPrenotazioniFolder(), "auto_confirm", False):
            api.content.transition(obj=booking, transition="confirm")
            booking.reindexObject(idxs="review_state")


# TODO: use the notify_on_after_transition_event method techique instead
def notify_on_move(booking, event):
    if not getattr(booking.getPrenotazioniFolder(), "notify_on_move", False):
        return
    if not getattr(booking, "email", ""):
        # booking does not have an email set
        return
    adapter = getMultiAdapter((booking, event), IPrenotazioneEmailMessage)
    if adapter:
        if adapter.message:
            send_email(adapter.message)


def send_email(msg):
    if not msg:
        logger.error("Could not send email due to no message was provided")
        return

    host = api.portal.get_tool(name="MailHost")
    registry = getUtility(IRegistry)
    encoding = registry.get("plone.email_charset", "utf-8")

    host.send(msg, charset=encoding)


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


def send_email_to_managers(booking, event):
    # skip email for vacation/out-of-office
    if is_migration():
        return

    if booking.isVacation():
        return
    if not getattr(booking, "email_responsabile", []):
        return

    adapter = getMultiAdapter(
        (booking, event), IPrenotazioneEmailMessage, name="notify_manager"
    )

    if adapter:
        if adapter.message:
            send_email(adapter.message)


def set_booking_code(booking, event):
    """
    set booking code. skip if we are importing old booking
    """
    if is_migration():
        return

    hash_obj = hashlib.blake2b(bytes(booking.UID(), encoding="utf8"), digest_size=3)
    hash_value = hash_obj.hexdigest().upper()
    setattr(booking, "booking_code", hash_value)
    return

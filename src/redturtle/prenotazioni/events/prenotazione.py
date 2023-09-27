# -*- coding: utf-8 -*-
import hashlib
from email.utils import formataddr, parseaddr
from logging import getLogger

from plone import api
from plone.app.event.base import default_timezone
from plone.registry.interfaces import IRegistry
from plone.stringinterp.interfaces import IStringSubstitution
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zope.component import getAdapter, getMultiAdapter, getUtility
from zope.i18n import translate

from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.utils import is_migration

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
    booking_folder = context.getPrenotazioniFolder()
    flags = {
        i: getattr(booking_folder, f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }
    if flags["confirm"] and flags["submit"]:
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

    booking_folder = booking.getPrenotazioniFolder()

    booking_operator_url = getAdapter(
        booking, IStringSubstitution, "booking_operator_url"
    )()

    email_list = getattr(booking_folder, "email_responsabile", "")
    if email_list:
        mail_template = api.content.get_view(
            name="manager_notification_mail",
            context=booking,
            request=booking.REQUEST,
        )
        booking_date = getattr(booking, "booking_date", None)
        parameters = {
            "company": getattr(booking, "company", ""),
            "booking_folder": booking_folder.title,
            "booking_url": booking_operator_url,
            "booking_date": booking_date.astimezone(
                default_timezone(as_tzinfo=True)
            ).strftime("%d/%m/%Y"),
            "booking_hour": booking_date.astimezone(
                default_timezone(as_tzinfo=True)
            ).strftime("%H:%M"),
            "booking_expiration_date": getattr(booking, "booking_expiration_date", ""),
            "description": getattr(booking, "description", ""),
            "email": getattr(booking, "email", ""),
            "fiscalcode": getattr(booking, "fiscalcode", ""),
            "gate": getattr(booking, "gate", ""),
            "phone": getattr(booking, "phone", ""),
            "staff_notes": getattr(booking, "staff_notes", ""),
            "booking_type": getattr(booking, "booking_type", ""),
            "title": getattr(booking, "title", ""),
        }
        mail_text = mail_template(**parameters)

        mailHost = api.portal.get_tool(name="MailHost")
        subject = translate(
            _(
                "new_booking_admin_notify_subject",
                default="New booking for ${context}",
                mapping={"context": booking_folder.title},
            ),
            context=booking.REQUEST,
        )
        for mail in email_list:
            if mail:
                mailHost.send(
                    mail_text,
                    mto=mail,
                    mfrom=get_mail_from_address(),
                    subject=subject,
                    charset="utf-8",
                    msg_type="text/html",
                )


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

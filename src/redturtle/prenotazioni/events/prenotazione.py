# -*- coding: utf-8 -*-
from Acquisition import aq_chain
from zope.component import getMultiAdapter
from plone import api

from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.adapters.booker import IBooker
from zope.i18n import translate
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from email.utils import formataddr
from email.utils import parseaddr
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from redturtle.prenotazioni import _


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
    booking_folder = None
    for item in booking.aq_chain:
        if getattr(item, "portal_type", "") == "PrenotazioniFolder":
            booking_folder = item
            break

    email_list = getattr(booking_folder, "email_responsabile", "")
    if email_list:
        mail_template = api.content.get_view(
            name="manager_notification_mail",
            context=booking,
            request=booking.REQUEST,
        )
        parameters = {
            "company": getattr(booking, "company", ""),
            "booking_folder": booking_folder.title,
            "booking_url": booking.absolute_url(),
            "booking_date": getattr(booking, "booking_date", ""),
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
                    immediate=True,
                )

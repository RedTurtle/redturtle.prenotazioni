# -*- coding: utf-8 -*-
from __future__ import print_function
from email.utils import formataddr
from email.utils import parseaddr
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from Products.CMFPlone.utils import getSiteEncoding
from redturtle.prenotazioni.adapters.booker import IBooker
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.i18n import translate
from redturtle.prenotazioni import _

import logging

logger = logging.getLogger(__name__)


def reallocate_gate(obj):
    """
    We have to reallocate the gate for this object

    Skip this step if we have a form.gate parameter in the request
    """
    context = obj.object

    if context.REQUEST.form.get("form.gate", "") and getattr(
        context, "gate", ""
    ):
        return

    container = context.getPrenotazioniFolder()
    booking_date = context.getData_prenotazione()
    new_gate = IBooker(container).get_available_gate(booking_date)
    context.gate = new_gate


def reallocate_container(obj):
    """
    If we moved Prenotazione to a new week we should move it
    """
    container = obj.object.getPrenotazioniFolder()
    IBooker(container).fix_container(obj.object)


def get_mail_host():
    """Get the MailHost object.

    Return None in case of problems.
    """
    portal = getSite()
    if portal is None:
        return None
    request = portal.REQUEST
    ctrlOverview = getMultiAdapter(
        (portal, request), name="overview-controlpanel"
    )
    mail_settings_correct = not ctrlOverview.mailhost_warning()
    if mail_settings_correct:
        mail_host = getToolByName(portal, "MailHost", None)
        return mail_host


def get_charset():
    """Character set to use for encoding the email.

    If encoding fails we will try some other encodings.  We hope
    to get utf-8 here always actually.

    The getSiteEncoding call also works when portal is None, falling
    back to utf-8.  But that is only on Plone 4, not Plone 3.  So we
    handle that ourselves.
    """
    charset = None
    portal = getSite()
    if IMailSchema is None:
        # Plone 4
        charset = portal.getProperty("email_charset", "")
    else:
        # Plone 5.0 and higher
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(
            IMailSchema, prefix="plone", check=False
        )
        charset = mail_settings.email_charset

    if not charset:
        charset = getSiteEncoding(portal)
    return charset


def get_mail_from_address():
    portal = getSite()
    if portal is None:
        return ""
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(
        IMailSchema, prefix="plone", check=False
    )
    from_address = mail_settings.email_from_address
    from_name = mail_settings.email_from_name

    if not from_address:
        return ""
    from_address = from_address.strip()
    mfrom = formataddr((from_name, from_address))
    if parseaddr(mfrom)[1] != from_address:
        # formataddr probably got confused by special characters.
        mfrom = from_address
    return mfrom


def add_booking_notify_manager(obj, event):
    folder = None
    for item in obj.aq_chain:
        if getattr(item, "portal_type", "") == "PrenotazioniFolder":
            folder = item
            break
    email_list = getattr(folder, "email_responsabile", "")
    if email_list:
        message = translate(
            _(
                "new_booking_admin_notify_message",
                default='New booking created for "${name}": ${url}',
                mapping={"name": obj.title, "url": obj.absolute_url()},
            ),
            context=obj.REQUEST,
        )
        subject = translate(
            _(
                "new_booking_admin_notify_subject",
                default="New booking for ${context}",
                mapping={"context": folder.title},
            ),
            context=obj.REQUEST,
        )
        for mail in email_list:
            if mail:
                api.portal.send_email(
                    recipient=mail,
                    sender=get_mail_from_address(),
                    subject=subject,
                    body=message,
                )

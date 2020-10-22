# -*- coding: utf-8 -*-
from __future__ import print_function
from redturtle.prenotazioni.adapters.booker import IBooker
from Acquisition import aq_parent, aq_inner
from zope.component.hooks import getSite
from zope.component import getMultiAdapter
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from email.utils import formataddr
from email.utils import parseaddr
from redturtle.prenotazioni import prenotazioniLogger as logger


def reallocate_gate(obj):
    '''
    We have to reallocate the gate for this object

    Skip this step if we have a form.gate parameter in the request
    '''
    context = obj.object

    if context.REQUEST.form.get('form.gate', '') and context.getGate():
        return

    container = context.getPrenotazioniFolder()
    booking_date = context.getData_prenotazione()
    new_gate = IBooker(container).get_available_gate(booking_date)
    context.setGate(new_gate)


def reallocate_container(obj):
    '''
    If we moved Prenotazione to a new week we should move it
    '''
    container = obj.object.getPrenotazioniFolder()
    IBooker(container).fix_container(obj.object)


def simple_send_mail(message, addresses, subject, immediate=False):
    """Send a notification email to the list of addresses.

    The method is called 'simple' because all the clever stuff should
    already have been done by the caller.

    message is passed without change to the mail host.  It should
    probably be a correctly encoded Message or MIMEText.

    One mail with the given message and subject is sent for each address.

    Starting with Plone 4 (Zope 2.12) by default the sending is deferred
    to the end of the transaction.  It seemed that this would mean that
    an exception during sending would roll back the transaction, so we
    passed immediate=True by default, catching the error and continuing.

    But this is not the case: Products/CMFPlone/patches/sendmail.py
    patches the email sending to not raise an error when the transaction
    is already finished.  So in case of problems the transaction is not
    rolled back.  (zope.sendmail 4.0 does this itself.)

    And that is fine for us: usually a problem with sending the email
    should not result in a transaction rollback or an error for the
    user.

    There is still the option to send immediately.  If you want this,
    you can pass immediate=False to this function.
    """
    mail_host = get_mail_host()
    if mail_host is None:
        logger.warn("Cannot send notification email: please configure "
                    "MailHost correctly.")
        # We print some info, which is perfect for checking in unit
        # tests.
        print('Subject =', subject)
        print('Addresses =', addresses)
        print('Message =')
        print(message)
        return

    mfrom = get_mail_from_address()
    header_charset = get_charset()

    for address in addresses:
        if not address:
            continue
        mail_host.send(
            message,
            mto=address,
            mfrom=mfrom,
            subject=subject,
            immediate=immediate,
            charset=header_charset)


def get_mail_host():
    """Get the MailHost object.

    Return None in case of problems.
    """
    portal = getSite()
    if portal is None:
        return None
    request = portal.REQUEST
    ctrlOverview = getMultiAdapter((portal, request),
                                   name='overview-controlpanel')
    mail_settings_correct = not ctrlOverview.mailhost_warning()
    if mail_settings_correct:
        mail_host = getToolByName(portal, 'MailHost', None)
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
    if portal is None:
        return DEFAULT_CHARSET
    if IMailSchema is None:
        # Plone 4
        charset = portal.getProperty('email_charset', '')
    else:
        # Plone 5.0 and higher
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(
            IMailSchema, prefix='plone', check=False)
        charset = mail_settings.email_charset

    if not charset:
        charset = getSiteEncoding(portal)
    return charset


def get_mail_from_address():
    portal = getSite()
    if portal is None:
        return ''
    if IMailSchema is None:
        # Plone 4
        from_address = portal.getProperty('email_from_address', '')
        from_name = portal.getProperty('email_from_name', '')
    else:
        # Plone 5.0 and higher
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(
            IMailSchema, prefix='plone', check=False)
        from_address = mail_settings.email_from_address
        from_name = mail_settings.email_from_name

    if not from_address:
        return ''
    from_address = from_address.strip()
    mfrom = formataddr((from_name, from_address))
    if parseaddr(mfrom)[1] != from_address:
        # formataddr probably got confused by special characters.
        mfrom = from_address
    return mfrom


def simple_send_mail(message, addresses, subject, immediate=False):
    """Send a notification email to the list of addresses.

    The method is called 'simple' because all the clever stuff should
    already have been done by the caller.

    message is passed without change to the mail host.  It should
    probably be a correctly encoded Message or MIMEText.

    One mail with the given message and subject is sent for each address.

    Starting with Plone 4 (Zope 2.12) by default the sending is deferred
    to the end of the transaction.  It seemed that this would mean that
    an exception during sending would roll back the transaction, so we
    passed immediate=True by default, catching the error and continuing.

    But this is not the case: Products/CMFPlone/patches/sendmail.py
    patches the email sending to not raise an error when the transaction
    is already finished.  So in case of problems the transaction is not
    rolled back.  (zope.sendmail 4.0 does this itself.)

    And that is fine for us: usually a problem with sending the email
    should not result in a transaction rollback or an error for the
    user.

    There is still the option to send immediately.  If you want this,
    you can pass immediate=False to this function.
    """
    mail_host = get_mail_host()
    if mail_host is None:
        logger.warn("Cannot send notification email: please configure "
                    "MailHost correctly.")
        # We print some info, which is perfect for checking in unit
        # tests.
        print('Subject =', subject)
        print('Addresses =', addresses)
        print('Message =')
        print(message)
        return

    mfrom = get_mail_from_address()
    header_charset = get_charset()
    for address in addresses:
        if not address:
            continue
        mail_host.send(
            message,
            mto=address,
            mfrom=mfrom,
            subject=subject,
            immediate=immediate,
            charset=header_charset)


def add_booking_notify_manager(obj, event):
    address = []
    address.append(aq_parent(aq_parent(aq_parent(aq_inner(obj)))).email_responsabile)
    message = "E' stata sottoposta una nuova prenotazione {0}: {1}".format(obj.title, obj.absolute_url()) 
    subject = "Nuova prenotazione"

    simple_send_mail(message, list(address), subject)

    
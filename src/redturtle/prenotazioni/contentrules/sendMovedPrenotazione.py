# -*- coding: utf-8 -*-
import six
from Acquisition import aq_inner
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules.actions import ActionAddForm
from plone.app.contentrules.actions import ActionEditForm
from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper
from plone.app.contentrules.browser.formhelper import EditForm
from plone.contentrules.rule.interfaces import IExecutable
from plone.contentrules.rule.interfaces import IRuleElementData
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError

from redturtle.prenotazioni import _


class IMovedPrenotazioneAction(Interface):

    """Definition of the configuration available for a mail action"""

    subject = schema.TextLine(
        title=_("Subject"),
        description=_("Subject of the message"),
        required=True,
    )

    source = schema.TextLine(
        title=_("Sender email"),
        description=_(
            "source_help",
            default="The email address that sends the email. If no email is "
            "provided here, it will use the address from portal.",
        ),
        required=False,
    )

    message = schema.Text(
        title=_("Message"),
        description=_(
            "message_help",
            default="Type in here the message that you want to mail. Some "
            "defined content can be replaced: ${title} will be replaced with"
            " booking title (user fullname). ${date} will be replaced with "
            "booking new date. ${url} will be replaced by the booking url. "
            "${portal} will be replaced by the title "
            "of the portal.",
        ),
        required=True,
    )


@implementer(IMovedPrenotazioneAction, IRuleElementData)
class MovedPrenotazioneAction(SimpleItem):

    """
    The implementation of the action defined before
    """

    subject = ""
    source = ""
    message = ""
    dest_addr = ""  # XXX ?

    element = "redturtle.prenotazioni.actions.MovedPrenotazione"

    @property
    def summary(self):
        return _("Email report to prenotazione owner")


@implementer(IExecutable)
@adapter(Interface, IMovedPrenotazioneAction, Interface)
class MailActionExecutor(object):

    """
    The executor for this action.
    """

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def check_uni(self, value):
        """
        Verifica il contenuto da rimpiazzare ed effettua la conversione unicode
        se necessario
        """
        if not isinstance(value, six.text_type):
            value = value.decode("utf-8")
        return value

    def __call__(self):
        mailhost = getToolByName(aq_inner(self.context), "MailHost")
        if not mailhost:
            raise ComponentLookupError(
                "You must have a Mailhost utility to " "execute this action"
            )
        source = self.element.source
        urltool = getToolByName(aq_inner(self.context), "portal_url")
        portal = urltool.getPortalObject()
        email_charset = portal.getProperty("email_charset")
        if not source:
            # no source provided, looking for the site wide from email
            # address
            from_address = portal.getProperty("email_from_address")
            if not from_address:
                raise ValueError(
                    "You must provide a source address for this "
                    "action or enter an email in the portal properties"
                )
            from_name = portal.getProperty("email_from_name")
            source = "%s <%s>" % (from_name, from_address)
        plone_view = portal.restrictedTraverse("@@plone")
        obj = self.event.object
        dest = obj.getEmail()
        message = self.element.message
        message = message.replace(
            "${date}", plone_view.toLocalizedTime(obj.getBooking_date())
        )
        message = message.replace("${url}", obj.absolute_url())
        message = message.replace("${title}", self.check_uni(obj.Title()))
        message = message.replace("${portal}", self.check_uni(portal.Title()))
        subject = self.element.subject
        subject = subject.replace("${url}", obj.absolute_url())
        subject = subject.replace("${title}", self.check_uni(obj.Title()))
        subject = subject.replace("${portal}", self.check_uni(portal.Title()))

        self.context.plone_log("sending to: %s" % dest)
        try:
            # sending mail in Plone 4
            mailhost.send(
                message,
                mto=dest,
                mfrom=source,
                subject=subject,
                charset=email_charset,
            )
        except Exception:
            # sending mail in Plone 3
            mailhost.secureSend(
                message,
                dest,
                source,
                subject=subject,
                subtype="plain",
                charset=email_charset,
                debug=False,
            )

        return True


class MovedPrenotazioneAddForm(ActionAddForm):

    """
    An add form for the mail action
    """

    schema = IMovedPrenotazioneAction
    label = _("Add moved booking Mail Action")
    description = _(
        "A mail action that sends email notify when a booking is moved "
        "in an other slot."
    )
    form_name = _("Configure element")
    Type = MovedPrenotazioneAction


class MovedPrenotazioneAddFormView(ContentRuleFormWrapper):
    form = MovedPrenotazioneAddForm


class MovedPrenotazioneEditForm(EditForm):

    """
    An edit form for the mail action
    """

    schema = IMovedPrenotazioneAction
    label = _("Edit moved booking Mail Action")
    description = _(
        "A mail action that sends email notify when a booking is moved in "
        "an other slot."
    )
    form_name = _("Configure element")


class MovedPrenotazioneEditFormView(ActionEditForm):
    form = MovedPrenotazioneEditForm

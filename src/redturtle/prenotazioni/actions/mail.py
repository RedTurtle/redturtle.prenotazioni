# -*- coding: utf-8 -*-
import six
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.contentrules.mailfromfield import logger
from collective.contentrules.mailfromfield.actions.mail import IMailFromFieldAction
from collective.contentrules.mailfromfield.actions.mail import (
    MailActionExecutor as BaseExecutor,
)
from plone.contentrules.rule.interfaces import IExecutable
from plone.dexterity.interfaces import IDexterityContainer
from plone.event.interfaces import IICalendar
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from six.moves import filter
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer

from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione


class MailActionExecutor(BaseExecutor):
    """The executor for this action."""

    def get_target_obj(self):
        """Get's the target object, i.e. the object that will provide the field
        with the email address
        """
        event_obj = self.event.object
        if event_obj.portal_type != "Prenotazione":
            return super().get_target_obj()
        target = self.element.target
        if target == "object":
            obj = self.context
        elif target == "parent":
            # this is the patch
            return event_obj.aq_parent
        elif target == "target":
            obj = event_obj
        else:
            raise ValueError(target)
        return aq_base(aq_inner(obj))

    def get_recipients(self):
        """
        The recipients of this mail
        """

        if self.event.object.portal_type != "Prenotazione":
            return super().get_recipients()

        # Try to load data from the target object
        fieldName = str(self.element.fieldName)
        obj = self.get_target_obj()

        attr = getattr(obj, fieldName)
        if hasattr(attr, "__call__"):
            recipients = attr()
            logger.debug("getting e-mail from %s method" % fieldName)
        else:
            recipients = attr
            logger.debug("getting e-mail from %s attribute" % fieldName)

        # now transform recipients in a iterator, if needed
        if type(recipients) == str or type(recipients) == six.text_type:  # noqa
            recipients = [str(recipients)]
        if not recipients:
            return []
        return list(filter(bool, recipients))

    def manage_attachments(self, msg):
        booking = self.event.object
        action = getattr(self.event, "action", "")
        if (
            not (action == "confirm" or IMovedPrenotazione.providedBy(self.event))
            or booking.portal_type != "Prenotazione"
        ):
            return
        cal = IICalendar(booking)
        ical = cal.to_ical()
        name = f"{booking.getId()}.ics"

        msg.add_attachment(
            ical,
            maintype="text",
            subtype="calendar",
            filename=name,
        )


@implementer(IExecutable)
@adapter(IPloneSiteRoot, IMailFromFieldAction, Interface)
class MailActionExecutorRoot(MailActionExecutor):
    """Registered for site root"""


@implementer(IExecutable)
@adapter(IDexterityContainer, IMailFromFieldAction, Interface)
class MailActionExecutorFolder(MailActionExecutor):
    """Registered for folderish content"""

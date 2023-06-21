# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.contentrules.mailfromfield import logger
from collective.contentrules.mailfromfield.actions.mail import IMailFromFieldAction
from collective.contentrules.mailfromfield.actions.mail import (
    MailActionExecutor as BaseExecutor,
)
from plone.contentrules.rule.interfaces import IExecutable
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from six.moves import filter
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from plone.event.interfaces import IICalendar
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione

import six


@implementer(IExecutable)
@adapter(IPloneSiteRoot, IMailFromFieldAction, Interface)
class MailActionExecutor(BaseExecutor):
    """The executor for this action."""

    def get_target_obj(self):
        """Get's the target object, i.e. the object that will provide the field
        with the email address
        """
        target = self.element.target
        if target == "object":
            obj = self.context
        elif target == "parent":
            obj = self.event.object.aq_parent
            # NEEDED JUST FOR PRENOTAZIONI...
            return obj
        elif target == "target":
            obj = self.event.object
        else:
            raise ValueError(target)
        return aq_base(aq_inner(obj))

    def get_recipients(self):
        """
        The recipients of this mail
        """
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
        if type(recipients) == str or type(recipients) == six.text_type:
            recipients = [str(recipients)]
        if not recipients:
            return []
        return list(filter(bool, recipients))

    def manage_attachments(self, msg):
        action = getattr(self.event, "action", "")
        if not (action == "confirm" or IMovedPrenotazione.providedBy(self.event)):
            return
        booking = self.event.object
        cal = IICalendar(booking)
        ical = cal.to_ical()
        name = f"{booking.getId()}.ics"

        msg.add_attachment(
            ical,
            maintype="text",
            subtype="calendar",
            filename=name,
        )

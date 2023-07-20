"""In this module we implemented the booking email templates which were used
    by plone contenttrules in previous verisions of the package"""

from logging import getLogger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from Acquisition import aq_chain
from zope.component import adapter, getAdapter
from zope.interface import implementer
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from Products.CMFCore.interfaces import IActionSucceededEvent
from plone import api
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from plone.event.interfaces import IICalendar

from redturtle.prenotazioni import _
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.content.prenotazioni_folder import (
    PrenotazioniFolder,
)


logger = getLogger(__name__)


class PrenotazioneEventEmailMessage:
    prenotazione = None
    event = None

    def __init__(self, prenotazione, event):
        self.prenotazione = prenotazione
        self.event = event

    @property
    def folder(self) -> PrenotazioniFolder:
        return [
            i
            for i in aq_chain(self.prenotazione)
            if getattr(i, "portal_type", "") == "PrenotazioniFolder"
        ][0]

    @property
    def message_subject(self) -> str:
        raise NotImplementedError("The method was not implemented")

    @property
    def message_text(self) -> MIMEText:
        raise NotImplementedError("The method was not implemented")

    @property
    def message(self) -> MIMEMultipart:
        error_msg = "Could not send notification email due to: {message}"
        mfrom = api.portal.get_registry_record("plone.email_from_address")
        recipient = self.prenotazione.email

        if not mfrom:
            logger.error(
                error_msg.format(
                    message="Email from address is not configured"
                )
            )
            return None

        if not recipient:
            logger.error(
                error_msg.format(
                    message="Could not find recipients for the email message"
                )
            )
            return None

        msg = MIMEMultipart()

        msg.attach(self.message_text)

        msg["Subject"] = self.message_subject
        msg["From"] = mfrom
        msg["To"] = recipient

        return msg


class PrenotazioneEventMessageICallMixIn:
    @property
    def message(self, *args, **kwargs):
        message = super().message(*args, **kwargs)

        icall = getAdapter((self.prenotazione,), IICalendar)

        message.attach(icall, "text/calendar")

        return message


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedEmailMessage(
    PrenotazioneEventEmailMessage, PrenotazioneEventMessageICallMixIn
):
    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.folder,
                f"notify_on_moved_subject",
                "",
            )
        )

    @property
    def message_text(self) -> MIMEText:
        return MIMEText(
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    getattr(
                        self.folder,
                        f"notify_on_moved_message",
                        None,
                    ),
                    "output",
                    "",
                )
            ),
            "html",
        )


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionEmailMessage(PrenotazioneEventEmailMessage):
    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.folder,
                f"notify_on_{self.event.transition and self.event.transition.__name__}_subject",
                "",
            )
        )

    @property
    def message_text(self) -> MIMEText:
        return MIMEText(
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    getattr(
                        self.folder,
                        f"notify_on_{self.event.transition and self.event.transition.__name__}_message",
                        None,
                    ),
                    "output",
                    "",
                )
            ),
            "html",
        )


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionEmaiICalllMessage(
    PrenotazioneAfterTransitionEmailMessage, PrenotazioneEventMessageICallMixIn
):
    pass

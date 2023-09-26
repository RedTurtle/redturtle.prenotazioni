# -*- coding: utf-8 -*-
"""In this module we implemented the booking email templates which were used
    by plone contenttrules in previous verisions of the package"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from plone import api
from plone.event.interfaces import IICalendar
from plone.stringinterp.interfaces import IContextWrapper, IStringInterpolator
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter, getAdapter
from zope.interface import implementer

from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione


class PrenotazioneEventEmailMessage:
    prenotazione = None
    event = None

    def __init__(self, prenotazione, event):
        self.prenotazione = prenotazione
        self.event = event

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
                error_msg.format(message="Email from address is not configured")
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


class PrenotazioneEventMessageICalMixIn:
    @property
    def message(self, *args, **kwargs):
        message = super().message

        if not message:
            logger.error(
                logger.error("Could not compose email due to no message was created")
            )
            return None

        message.add_header("Content-class", "urn:content-classes:calendarmessage")

        ical = getAdapter(object=self.prenotazione, interface=IICalendar)
        name = f"{self.prenotazione.getId()}.ics"
        icspart = MIMEText(ical.to_ical().decode("utf-8"), "calendar")

        icspart.add_header("Filename", name)
        icspart.add_header("Content-Disposition", f"attachment; filename={name}")

        message.attach(icspart)

        return message


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedICalEmailMessage(
    PrenotazioneEventMessageICalMixIn, PrenotazioneEventEmailMessage
):
    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_on_move_subject",
                "",
            )
        )

    @property
    def message_text(self) -> MIMEText:
        return MIMEText(
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    self.prenotazione.getPrenotazioniFolder(),
                    "notify_on_move_message",
                    None,
                ),
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
                self.prenotazione.getPrenotazioniFolder(),
                f"notify_on_{self.event.transition and self.event.transition.__name__}_subject",
                "",
            )
        )

    @property
    def message_text(self) -> MIMEText:
        return MIMEText(
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    self.prenotazione.getPrenotazioniFolder(),
                    f"notify_on_{self.event.transition and self.event.transition.__name__}_message",
                    None,
                ),
            ),
            "html",
        )


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionEmailICalMessage(
    PrenotazioneEventMessageICalMixIn, PrenotazioneAfterTransitionEmailMessage
):
    pass

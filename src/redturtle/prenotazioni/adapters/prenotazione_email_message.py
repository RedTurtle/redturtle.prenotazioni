# -*- coding: utf-8 -*-
"""In this module we implemented the booking email templates which were used
    by plone contenttrules in previous verisions of the package"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from plone import api
from plone.app.event.base import default_timezone
from plone.event.interfaces import IICalendar
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from plone.stringinterp.interfaces import IStringSubstitution
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import getAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.lifecycleevent import IObjectAddedEvent

from redturtle.prenotazioni import _
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
        name = f"{self.prenotazione.getId()}.ics"

        ical = getAdapter(object=self.prenotazione, interface=IICalendar)
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


@implementer(IPrenotazioneEmailMessage)
@adapter(IPrenotazione, IObjectAddedEvent)
class PrenotazioneManagerEmailMessage(PrenotazioneEventEmailMessage):
    def __init__(self, prenotazione, event):
        super().__init__(prenotazione=prenotazione, event=event)

        # set request annotation to mark it as manager notification.
        # this will be used in ical adapter to change the title of the ical item
        annotations = IAnnotations(prenotazione.REQUEST)
        annotations["ical_manager_notification"] = True

    @property
    def message(self) -> MIMEMultipart:
        """
        customized to send Bcc instead To
        """
        error_msg = "Could not send notification email due to: {message}"
        mfrom = api.portal.get_registry_record("plone.email_from_address")
        bcc = ", ".join(getattr(self.prenotazione, "email_responsabile", []))

        if not mfrom:
            logger.error(
                error_msg.format(message="Email from address is not configured")
            )
            return None

        msg = MIMEMultipart()

        msg.attach(self.message_text)

        msg["Subject"] = self.message_subject
        msg["From"] = mfrom
        msg["Bcc"] = bcc

        # ical part
        msg.add_header("Content-class", "urn:content-classes:calendarmessage")
        name = f"{self.prenotazione.getId()}.ics"

        ical = getAdapter(object=self.prenotazione, interface=IICalendar)
        icspart = MIMEText(ical.to_ical().decode("utf-8"), "calendar")

        icspart.add_header("Filename", name)
        icspart.add_header("Content-Disposition", f"attachment; filename={name}")

        msg.attach(icspart)
        return msg

    @property
    def message_subject(self) -> str:
        booking_folder = self.prenotazione.getPrenotazioniFolder()
        return translate(
            _(
                "new_booking_admin_notify_subject",
                default="New booking for ${context}",
                mapping={"context": booking_folder.title},
            ),
            context=self.prenotazione.REQUEST,
        )

    @property
    def message_text(self) -> MIMEText:
        booking = self.prenotazione
        booking_folder = booking.getPrenotazioniFolder()
        booking_operator_url = getAdapter(
            booking, IStringSubstitution, "booking_operator_url"
        )()

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
        return MIMEText(mail_template(**parameters), "html")

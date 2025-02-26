# -*- coding: utf-8 -*-
"""Email notification templates"""

from email.charset import Charset
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from plone import api
from plone.app.event.base import default_timezone
from plone.event.interfaces import IICalendar
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from plone.stringinterp.interfaces import IStringSubstitution
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from redturtle.prenotazioni import _
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import getAdapter
from zope.interface import implementer
from zope.interface import Interface

import os
import qrcode


CTE = os.environ.get("MAIL_CONTENT_TRANSFER_ENCODING", None)


class PrenotazioneEmailMessage:
    prenotazione = None
    event = None
    error_msg = "Could not send notification email due to: {message}"

    def __init__(self, prenotazione, event):
        self.prenotazione = prenotazione
        self.event = event

    @property
    def message_history(self) -> str:
        raise NotImplementedError("The method was not implemented")

    @property
    def message_subject(self) -> str:
        raise NotImplementedError("The method was not implemented")

    @property
    def message_text(self) -> MIMEText:
        raise NotImplementedError("The method was not implemented")

    @property
    def prenotazioni_folder(self):
        return self.prenotazione.getPrenotazioniFolder()

    @property
    def message_from(self) -> str:
        """
        Return the proper from address.
        If set in PrenotazioniFolder, return that value, otherwise, return the site one.
        """
        mfrom = api.portal.get_registry_record("plone.email_from_address")
        return getattr(self.prenotazioni_folder, "email_from", "") or mfrom

    @property
    def message(self) -> MIMEMultipart:
        mfrom = self.message_from
        recipient = self.prenotazione.email

        if not mfrom:
            logger.error(
                self.error_msg.format(message="Email from address is not configured")
            )
            return None

        if not recipient:
            logger.error(
                self.error_msg.format(
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


class PrenotazioneEventMessageMixIn:
    @property
    def message(self, *args, **kwargs):
        message = super().message

        if not message:
            logger.error(
                logger.error("Could not compose email due to no message was created")
            )
            return None

        # TODO: verificare la resa nelle email del QRCode come allegato,
        #       e se non soddisfacente spostarlo nel messaggio (che mi pare html)
        #       cfr:https://mailtrap.io/blog/embedding-images-in-html-email-have-the-rules-changed/
        #       <p><img src="cid:qrcode"></img></p>
        if (
            getattr(self.prenotazioni_folder, "attach_qrcode", None)
            and self.prenotazione.getBookingCode()
        ):
            # Generate QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.prenotazione.getBookingCode())
            qr.make(fit=True)
            img = qr.make_image()
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()
            qrcodepart = MIMEImage(img_bytes, name="qrcode")
            qrcodepart.add_header(
                "Content-Disposition",
                f"attachment; filename={self.prenotazione.getBookingCode()}.png",
            )
            message.attach(qrcodepart)

        # ICAL
        message.add_header("Content-class", "urn:content-classes:calendarmessage")
        name = f"{self.prenotazione.getId()}.ics"
        ical = getAdapter(object=self.prenotazione, interface=IICalendar)
        icspart = MIMEText(ical.to_ical().decode("utf-8"), "calendar")
        icspart.add_header("Filename", name)
        icspart.add_header("Content-Disposition", f"attachment; filename={name}")
        message.attach(icspart)

        return message


# BBB: nel caso la classe viene usata, con questo nome, da eventuali addon
PrenotazioneEventMessageICalMixIn = PrenotazioneEventMessageMixIn


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedICalEmailMessage(
    PrenotazioneEventMessageMixIn, PrenotazioneEmailMessage
):
    @property
    def message_history(self) -> str:
        return api.portal.translate(
            _(
                "history_email_reschedule_sent",
                default="Email message about the booking reschedule was sent",
            )
        )

    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_on_move_subject", "")
        )

    @property
    def message_text(self) -> MIMEText:
        text = IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_on_move_message", None),
        )
        if CTE:
            cs = Charset("utf-8")
            cs.body_encoding = CTE  # e.g. 'base64'
            return MIMEText(text, "html", cs)
        else:
            return MIMEText(text, "html")


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionEmailMessage(PrenotazioneEmailMessage):
    @property
    def message_history(self) -> str:
        transition = (
            self.event.transition
            and api.portal.translate(self.event.transition.title)
            or ""
        )
        return api.portal.translate(
            _(
                "history_email_transition_sent",
                "Email message about the ${transition} transition was sent",
                mapping={"transition": transition},
            ),
        )

    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazioni_folder,
                f"notify_on_{self.event.transition and self.event.transition.__name__}_subject",
                "",
            )
        )

    @property
    def message_text(self) -> MIMEText:
        text = IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazioni_folder,
                f"notify_on_{self.event.transition and self.event.transition.__name__}_message",
                None,
            ),
        )
        # TODO: verificare la resa nelle email del QRCode come allegato, e se non soddisfacente
        #       spostarlo nel testo del messaggio
        if CTE:
            cs = Charset("utf-8")
            cs.body_encoding = CTE  # e.g. 'base64'
            return MIMEText(text, "html", cs)
        else:
            return MIMEText(text, "html")


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionEmailICalMessage(
    PrenotazioneEventMessageMixIn, PrenotazioneAfterTransitionEmailMessage
):
    pass


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneReminderEmailMessage(PrenotazioneEmailMessage):
    @property
    def message_history(self) -> str:
        return api.portal.translate(
            _("history_reminder_sent", default="Email reminder was sent")
        )

    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_as_reminder_subject", "")
        )

    @property
    def message_text(self) -> MIMEText:
        html = IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_as_reminder_message", None),
        )
        if CTE:
            cs = Charset("utf-8")
            cs.body_encoding = CTE  # e.g. 'base64'
            return MIMEText(html, "html", cs)
        else:
            return MIMEText(html, "html")


# NOTE: We are talking about the booking created message here
# TODO: If this logic is being used in the booker, so this message generation
#       must be moved to the main module. It is very bad approach to keep this code here(in behavior)
@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, Interface)
class PrenotazioneManagerEmailMessage(
    PrenotazioneEventMessageMixIn, PrenotazioneEmailMessage
):
    """
    This is not fired from an event, but used in booker.
    """

    def __init__(self, prenotazione, request):
        self.prenotazione = prenotazione
        self.request = request
        # set request annotation to mark it as manager notification.
        # this will be used in ical adapter to change the title of the ical item
        annotations = IAnnotations(prenotazione.REQUEST)
        annotations["ical_manager_notification"] = True

    @property
    def message_history(self) -> str:
        return api.portal.translate(
            _(
                "history_email_manager_notification_sent",
                default="Email notification was sent to booking manager",
            ),
        )

    @property
    def message(self) -> MIMEMultipart:
        """
        customized to send Bcc instead To
        """
        mfrom = self.message_from
        bcc = ", ".join(getattr(self.prenotazione, "email_responsabile", []))

        if not mfrom:
            logger.error(
                self.error_msg.format(message="Email from address is not configured")
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
        """
        return subject
        """
        booking_type = getattr(self.prenotazione, "booking_type", "")
        booking_code = self.prenotazione.getBookingCode()
        date = self.prenotazione.booking_date.strftime("%d-%m-%Y %H:%M")
        return f"[{booking_type}] {date} {booking_code}"

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
        text = mail_template(**parameters)
        if CTE:
            cs = Charset("utf-8")
            cs.body_encoding = CTE  # e.g. 'base64'
            return MIMEText(text, "html", cs)
        else:
            return MIMEText(text, "html")


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, Interface)
class PrenotazioneCanceledManagerEmailMessage(PrenotazioneManagerEmailMessage):
    """
    This is not fired from an event, but used in booker.
    """

    @property
    def message_subject(self) -> str:
        """
        return subject
        """
        booking_type = getattr(self.prenotazione, "booking_type", "")
        booking_code = self.prenotazione.getBookingCode()
        date = self.prenotazione.booking_date.strftime("%d-%m-%Y %H:%M")

        booking_canceled = api.portal.translate(
            _("booking_canceled_mail_subject_part", default="Booking canceled: ")
        )
        return f"{booking_canceled} [{booking_type}] {date} {booking_code}"

    @property
    def message(self) -> MIMEMultipart:
        """
        customized to send Bcc instead To
        """
        mfrom = self.message_from
        bcc = ", ".join(getattr(self.prenotazione, "email_responsabile", []))

        if not mfrom:
            logger.error(
                self.error_msg.format(message="Email from address is not configured")
            )
            return None

        msg = MIMEMultipart()

        msg.attach(self.message_text)
        msg["Subject"] = self.message_subject
        msg["From"] = mfrom
        msg["Bcc"] = bcc

        return msg


@implementer(IBookingEmailMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneRemovedEmailMessage(PrenotazioneEmailMessage):
    @property
    def message_subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_as_removed_subject", "")
        )

    @property
    def message_text(self) -> MIMEText:
        text = IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(self.prenotazioni_folder, "notify_as_removed_message", None),
        )
        if CTE:
            cs = Charset("utf-8")
            cs.body_encoding = CTE  # e.g. 'base64'
            return MIMEText(text, "html", cs)
        else:
            return MIMEText(text, "html")

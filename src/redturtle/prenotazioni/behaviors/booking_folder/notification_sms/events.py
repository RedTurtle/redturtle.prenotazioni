# -*- coding: utf-8 -*-
from logging import getLogger

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IPrenotazioneSMSMessage

logger = getLogger(__name__)


def send_notification_on_transition(context, event) -> None:
    booking_folder = context.getPrenotazioniFolder()
    flags = {
        i: getattr(booking_folder, f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }

    if flags["confirm"] and getattr(booking_folder, "auto_confirm", False):
        flags["submit"] = False

    if flags.get(
        event.transition and event.transition.__name__ or "",
        False,
    ):
        if not getattr(context, "email", ""):
            # booking does not have an email set
            return
        message_adapter = getMultiAdapter(
            (context, event),
            IPrenotazioneSMSMessage,
            name=event.transition.__name__,
        )

        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_sms_sender",
        )

        if message_adapter and message_adapter.message:
            sender_adapter.send()


# TODO: use the notify_on_after_transition_event method techique instead
def notify_on_move(booking, event):
    if not getattr(booking.getPrenotazioniFolder(), "notify_on_move", False):
        return
    if not getattr(booking, "email", ""):
        # booking does not have an email set
        return
    message_adapter = getMultiAdapter((booking, event), IPrenotazioneSMSMessage)
    sender_adapter = getMultiAdapter(
        (message_adapter, booking, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_sms_sender",
    )
    if message_adapter and message_adapter.message:
        sender_adapter.send()


def send_booking_reminder(context, event):
    message_adapter = getMultiAdapter(
        (context, event),
        IPrenotazioneSMSMessage,
        name="reminder_notification_sms_message",
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    if message_adapter and message_adapter.message:
        sender_adapter.send()

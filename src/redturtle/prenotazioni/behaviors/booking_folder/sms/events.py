# -*- coding: utf-8 -*-

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingSMSMessage
from redturtle.prenotazioni.utilities import handle_exception_by_log

from . import INotificationSMS


def booking_folder_provides_current_behavior(booking):
    return INotificationSMS.providedBy(booking.getPrenotazioniFolder())


@handle_exception_by_log
def send_notification_on_transition(context, event) -> None:
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    flags = booking_folder.get_notification_flags()

    if flags["confirm"] and getattr(booking_folder, "auto_confirm", False):
        flags["submit"] = False

    if event.transition and flags.get(event.transition.__name__):
        if not getattr(context, "phone", ""):
            # booking does not have an phone set
            return

        message_adapter = getMultiAdapter(
            (context, event),
            IBookingSMSMessage,
        )

        if message_adapter and message_adapter.message:
            sender_adapter = getMultiAdapter(
                (message_adapter, context, getRequest()),
                IBookingNotificationSender,
                name="booking_transition_sms_sender",
            )
            sender_adapter.send()


@handle_exception_by_log
def notify_on_move(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    if not getattr(booking_folder, "notify_on_move", False):
        return
    # XXX: il controllo immagino sia altrove e deve controllare
    #      non solo se l'email è presente ma anche se le notifiche email
    #      sono attive
    # if not getattr(context, "email", ""):
    #     # booking does not have an email set
    #     return
    message_adapter = getMultiAdapter((context, event), IBookingSMSMessage)
    if message_adapter and message_adapter.message:
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_sms_sender",
        )
        sender_adapter.send()


@handle_exception_by_log
def send_booking_reminder(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingSMSMessage,
        name="reminder_notification_sms_message",
    )
    if message_adapter and message_adapter.message:
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_sms_sender",
        )
        sender_adapter.send()

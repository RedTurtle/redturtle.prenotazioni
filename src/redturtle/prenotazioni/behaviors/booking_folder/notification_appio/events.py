# -*- coding: utf-8 -*-

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni.behaviors.booking_folder import (
    get_booking_folder_notification_flags,
)
from redturtle.prenotazioni.interfaces import IBookingAPPIoMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.utilities import handle_exception_by_log

from .notification_appio import INotificationAppIO


def booking_folder_provides_current_behavior(booking):
    return INotificationAppIO.providedBy(booking.getPrenotazioniFolder())


@handle_exception_by_log
def send_notification_on_transition(context, event) -> None:
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    flags = get_booking_folder_notification_flags(booking_folder)

    if flags["confirm"] and getattr(booking_folder, "auto_confirm", False):
        flags["submit"] = False

    if flags.get(
        event.transition and event.transition.__name__ or "",
        False,
    ):
        message_adapter = getMultiAdapter(
            (context, event),
            IBookingAPPIoMessage,
        )

        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_appio_sender",
        )

        if message_adapter and message_adapter.message:
            sender_adapter.send()


# TODO: use the notify_on_after_transition_event method techique instead
@handle_exception_by_log
def notify_on_move(booking, event):
    if not booking_folder_provides_current_behavior(booking):
        return

    if not getattr(booking.getPrenotazioniFolder(), "notify_on_move", False):
        return

    message_adapter = getMultiAdapter((booking, event), IBookingAPPIoMessage)
    sender_adapter = getMultiAdapter(
        (message_adapter, booking, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_appio_sender",
    )
    if message_adapter and message_adapter.message:
        sender_adapter.send()


@handle_exception_by_log
def send_booking_reminder(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingAPPIoMessage,
        name="reminder_notification_appio_message",
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_appio_sender",
    )

    if message_adapter and message_adapter.message:
        sender_adapter.send()

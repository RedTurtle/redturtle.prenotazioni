# -*- coding: utf-8 -*-
from functools import partial

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni.interfaces import IBookingAPPIoMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.utilities import handle_exception_by_log

from .. import notify_the_message_failure
from . import INotificationAppIO


def booking_folder_provides_current_behavior(booking):
    return INotificationAppIO.providedBy(booking.getPrenotazioniFolder())


notify_the_message_failure = partial(notify_the_message_failure, gateway_type="AppIO")


@handle_exception_by_log
@notify_the_message_failure
def send_notification_on_transition(context, event) -> None:
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    flags = booking_folder.get_notification_flags()

    if flags["confirm"] and getattr(booking_folder, "auto_confirm", False):
        flags["submit"] = False

    if event.transition and flags.get(event.transition.__name__):
        message_adapter = getMultiAdapter(
            (context, event),
            IBookingAPPIoMessage,
        )

        if message_adapter and message_adapter.message:
            sender_adapter = getMultiAdapter(
                (message_adapter, context, getRequest()),
                IBookingNotificationSender,
                name="booking_transition_appio_sender",
            )
            sender_adapter.send()


@handle_exception_by_log
@notify_the_message_failure
def notify_on_move(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    if not getattr(booking_folder, "notify_on_move", False):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingAPPIoMessage,
    )
    if message_adapter and message_adapter.message:
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_appio_sender",
        )
        sender_adapter.send()


@handle_exception_by_log
@notify_the_message_failure
def send_booking_reminder(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingAPPIoMessage,
        name="reminder_notification_appio_message",
    )

    if message_adapter and message_adapter.message:
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_appio_sender",
        )
        sender_adapter.send()


@handle_exception_by_log
@notify_the_message_failure
def send_booking_removed(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingAPPIoMessage,
        name="removed_notification_appio_message",
    )

    if message_adapter and message_adapter.message:
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_appio_sender",
        )
        sender_adapter.send()

# -*- coding: utf-8 -*-
from functools import partial

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.utilities import handle_exception_by_log

from .. import notify_the_message_failure
from . import INotificationEmail

notify_the_message_failure = partial(notify_the_message_failure, gateway_type="Email")


def booking_folder_provides_current_behavior(booking):
    return INotificationEmail.providedBy(booking.getPrenotazioniFolder())


@handle_exception_by_log
@notify_the_message_failure
def send_email_notification_on_transition(context, event) -> None:
    if not booking_folder_provides_current_behavior(context):
        return
    booking_folder = context.getPrenotazioniFolder()
    flags = booking_folder.get_notification_flags()

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
            IBookingEmailMessage,
        )

        if message_adapter and message_adapter.message:
            sender_adapter = getMultiAdapter(
                (message_adapter, context, getRequest()),
                IBookingNotificationSender,
                name="booking_transition_email_sender",
            )
            sender_adapter.send()


# TODO: use the notify_on_after_transition_event method techique instead


@handle_exception_by_log
@notify_the_message_failure
def notify_on_move(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    booking_folder = context.getPrenotazioniFolder()
    if not getattr(booking_folder, "notify_on_move", False):
        return
    if not getattr(context, "email", ""):
        # booking does not have an email set
        return
    message_adapter = getMultiAdapter((context, event), IBookingEmailMessage)
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()


@handle_exception_by_log
@notify_the_message_failure
def send_booking_reminder(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingEmailMessage,
        name="reminder_notification_email_message",
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()


@notify_the_message_failure
def send_booking_removed(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingEmailMessage,
        name="removed_notification_email_message",
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()


def send_booking_canceled_to_managers(booking, event):
    """
    Send email notification for managers
    """
    if (
        event.transition is None
        or not getattr(event.transition, "id", None) == "cancel"
    ):
        return

    if not booking_folder_provides_current_behavior(booking):
        return

    if booking.isVacation():
        return

    if not getattr(booking.getPrenotazioniFolder(), "email_responsabile", []):
        return

    request = getRequest()

    message_adapter = getMultiAdapter(
        (booking, request),
        IBookingEmailMessage,
        name="notify_manager_booking_canceled",
    )

    sender_adapter = getMultiAdapter(
        (message_adapter, booking, request),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send(force=True)

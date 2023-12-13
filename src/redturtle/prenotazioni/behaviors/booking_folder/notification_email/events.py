# -*- coding: utf-8 -*-
from logging import getLogger

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from redturtle.prenotazioni import is_migration
from redturtle.prenotazioni.behaviors.booking_folder import (
    get_booking_folder_notification_flags,
)
from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.utilities import handle_exception_by_log

from .notification_email import INotificationEmail

logger = getLogger(__name__)


def booking_folder_provides_current_behavior(booking):
    return INotificationEmail.providedBy(booking.getPrenotazioniFolder())


@handle_exception_by_log
def send_email_notification_on_transition(context, event) -> None:
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
        if not getattr(context, "email", ""):
            # booking does not have an email set
            return
        message_adapter = getMultiAdapter(
            (context, event),
            IBookingEmailMessage,
        )
        sender_adapter = getMultiAdapter(
            (message_adapter, context, getRequest()),
            IBookingNotificationSender,
            name="booking_transition_email_sender",
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
    if not getattr(booking, "email", ""):
        # booking does not have an email set
        return
    message_adapter = getMultiAdapter((booking, event), IBookingEmailMessage)
    sender_adapter = getMultiAdapter(
        (message_adapter, booking, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()


@handle_exception_by_log
def send_booking_reminder(context, event):
    if not booking_folder_provides_current_behavior(context):
        return

    message_adapter = getMultiAdapter(
        (context, event),
        IBookingEmailMessage,
        name="reminder_notification_message",
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, context, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()


@handle_exception_by_log
def send_email_to_managers(booking, event):
    if not booking_folder_provides_current_behavior(booking):
        return

    # skip email for vacation/out-of-office
    if is_migration():
        return

    if booking.isVacation():
        return
    if not getattr(booking, "email_responsabile", []):
        return

    message_adapter = getMultiAdapter(
        (booking, event), IBookingEmailMessage, name="notify_manager"
    )
    sender_adapter = getMultiAdapter(
        (message_adapter, booking, getRequest()),
        IBookingNotificationSender,
        name="booking_transition_email_sender",
    )

    sender_adapter.send()

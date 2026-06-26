# -*- coding: utf-8 -*-
from functools import wraps
from Products.CMFCore.utils import getToolByName
from redturtle.prenotazioni import _
from zope.annotation.interfaces import IAnnotations

# Annotation key used to collect, on the current request, the notifications
# that have actually been sent while handling it. This allows endpoints (ie.
# @booking-notify) to report back to the caller which notifications were sent.
SENT_NOTIFICATIONS_ANNOTATION_KEY = "redturtle.prenotazioni.sent_notifications"


def reset_sent_notifications(request):
    """Initialize (or clear) the list of sent notifications on the request."""
    if request is None:
        return
    IAnnotations(request)[SENT_NOTIFICATIONS_ANNOTATION_KEY] = []


def record_sent_notification(request, gateway, recipient="", message=""):
    """Record that a notification has been sent on the current request.

    gateway: the gateway used (ie. "email", "sms", "appio")
    recipient: the recipient of the notification (email, phone, fiscalcode...)
    message: an human readable description of the sent message
    """
    if request is None:
        return
    annotations = IAnnotations(request)
    sent = annotations.get(SENT_NOTIFICATIONS_ANNOTATION_KEY, None)
    if sent is None:
        sent = []
        annotations[SENT_NOTIFICATIONS_ANNOTATION_KEY] = sent
    sent.append(
        {
            "gateway": gateway,
            "recipient": recipient,
            "message": message,
        }
    )


def get_sent_notifications(request):
    """Return the list of notifications sent while handling the request."""
    if request is None:
        return []
    return IAnnotations(request).get(SENT_NOTIFICATIONS_ANNOTATION_KEY, [])


def get_booking_folder_notification_flags(booking_folder):
    return {
        i: getattr(booking_folder, f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }


def write_message_to_object_history(object, message):
    """Write a message to object versioning history"""
    pr = getToolByName(object, "portal_repository")
    pr.save(object, message)


def notify_the_message_failure(func, gateway_type=""):
    """Decorator to write the errors during the message senditg to the booking history"""

    @wraps(func)
    def inner(context, event, *args, **kwargs):
        try:
            func(context, event, *args, *kwargs)
        except Exception as e:
            write_message_to_object_history(
                object=context,
                message=_(
                    "Could not send {gateway_type} message due to internal errors"
                ).format(gateway_type=gateway_type),
            )

            raise e

    return inner


# Obsolete. Earlier it was used to manage the different notification types cross logics.
class BookingNotificationSupervisorUtility:
    """Supervisor to allow/deny the specific
    notification type according to business logic"""

    def is_email_message_allowed(self, booking):
        if getattr(
            booking.getPrenotazioniFolder(), "notifications_email_enabled", False
        ) and getattr(booking, "email", None):
            return True

        return False

    # NOTE: Will be extended in the future
    def is_appio_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_appio_enabled", False
        ):
            return False

        if not booking.fiscalcode:
            return False

        return True

    def is_sms_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_sms_enabled", False
        ):
            return False

        if not booking.phone:
            return False

        return True

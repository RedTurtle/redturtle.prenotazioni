# -*- coding: utf-8 -*-
import os

from redturtle.prenotazioni.io_tools.api import Api


def get_booking_folder_notification_flags(booking_folder):
    return {
        i: getattr(booking_folder, f"notify_on_{i}", False)
        for i in ("confirm", "submit", "refuse")
    }


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

        if self._check_user_appio_subscription_to_booking_type(booking):
            return True

        return False

    def is_sms_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_sms_enabled", False
        ):
            return False

        if self.is_email_message_allowed(booking):
            return False

        if self.is_appio_message_allowed(booking):
            return False

        if booking.phone:
            return True

        return False

    def _check_user_appio_subscription_to_booking_type(self, booking):
        service_code = getattr(booking.get_booking_type(), "service_code", "")

        if not service_code:
            return False

        return Api(secret=os.environ.get(service_code)).is_service_activated(
            booking.fiscalcode
        )

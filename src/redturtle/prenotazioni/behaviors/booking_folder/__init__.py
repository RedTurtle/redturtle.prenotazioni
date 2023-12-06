# -*- coding: utf-8 -*-
class BookingNotificationSupervisorUtility:
    """Supervisor to allow/deny the specific
    notification type according to business logic"""

    def is_email_message_allowed(self, booking):
        if getattr(
            booking.getPrenotazioniFolder(), "notifications_email_enabled", False
        ):
            return True

        return False

    # NOTE: Will be extended in the future
    def is_appio_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_appio_enabled", False
        ):
            return False

        fiscalcode = booking.fiscalcode

        if not fiscalcode:
            return False

        if self.check_user_appio_subscription_to_booking_type(booking):
            return True

    def is_sms_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_sms_enabled", False
        ):
            return False

        if not self.is_appio_message_allowed(booking):
            if booking.phone:
                return True

        return False

    def check_user_appio_subscription_to_booking_type(self, booking):
        return True

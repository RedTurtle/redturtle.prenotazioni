# -*- coding: utf-8 -*-
from .appio.adapters import app_io_allowed_for


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

        return True

    def app_io_allowed_for(sefl, fiscalcode, service_code):
        return app_io_allowed_for(fiscalcode, service_code=service_code)

    def is_sms_message_allowed(self, booking):
        if not getattr(
            booking.getPrenotazioniFolder(), "notifications_sms_enabled", False
        ):
            return False

        if not booking.phone:
            return False

        if self.is_email_message_allowed(booking):
            return False

        # if user is potentially notified by App IO, do not send sms
        if self.is_appio_message_allowed(booking):
            # XXX: questo sarebbe dovuto essere nell'adapter per App IO, ma l'adapter
            #      richiede a suo volta un message_adapter ...
            booking_type = booking.get_booking_type()
            service_code = getattr(booking_type, "service_code", None)
            fiscalcode = getattr(booking, "fiscalcode", None)
            if (
                fiscalcode
                and service_code
                and self.app_io_allowed_for(fiscalcode, service_code)
            ):
                return False

        return True

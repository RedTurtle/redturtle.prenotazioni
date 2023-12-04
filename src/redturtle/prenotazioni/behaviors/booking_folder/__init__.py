class BookingNotificationSupervisorUtility:
    """Supervisor to allow/deny the specific
    notification type according to business logic"""

    def is_email_message_allowed(self, booking):
        return True

    # NOTE: Will be extended in the future
    def is_appio_message_allowed(self, booking):
        fiscalcode = booking.fiscalcode

        if not fiscalcode:
            return False

        return True

    def is_sms_message_allowed(self, booking):
        if not self.is_appio_message_allowed:
            if booking.email:
                return True

        return False

    def check_user_appio_subscription(self, fiscalcode):
        pass

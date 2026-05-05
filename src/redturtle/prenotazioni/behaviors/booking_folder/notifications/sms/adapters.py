# -*- coding: utf-8 -*-

from zope.component import adapter, getUtility
from zope.interface import Interface, implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import (
    IBookingNotificationSender,
    IBookingNotificatorSupervisorUtility,
    IBookingSMSMessage,
)

from .. import write_message_to_object_history


@implementer(IBookingNotificationSender)
@adapter(IBookingSMSMessage, IPrenotazione, Interface)
class BookingNotificationSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self):
        if self.is_notification_allowed():
            # dont foget to write the history log about sending
            # self.write_message_to_booking_history(self.booking, self.message_adapter.message_history)
            raise NotImplementedError("The method was not implemented")

    def is_notification_allowed(self):
        if getUtility(
            IBookingNotificatorSupervisorUtility,
        ).is_sms_message_allowed(self.booking):
            return True
        return False

    def write_message_to_booking_history(self):
        write_message_to_object_history(
            self.booking, self.message_adapter.message_history
        )

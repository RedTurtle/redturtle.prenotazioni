# -*- coding: utf-8 -*-

from zope.component import adapter
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IBookingSMSMessage


@implementer(IBookingNotificationSender)
@adapter(IBookingSMSMessage, IPrenotazione, Interface)
class BookingNotificationSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self):
        if self.is_notification_allowed():
            raise NotImplementedError("The method was not implemented")

    def is_notification_allowed(self):
        if getUtility(
            IBookingNotificatorSupervisorUtility,
        ).is_sms_message_allowed(self.booking):
            return True
        return False

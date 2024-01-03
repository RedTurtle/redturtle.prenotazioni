# -*- coding: utf-8 -*-
from plone import api
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.behaviors.booking_folder.notification_sms.adapters import (
    BookingNotificationSender,
)
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingSMSMessage
from redturtle.prenotazioni.staging.interfaces import IRedturtlePrenotazioniStagingLayer


@implementer(IBookingNotificationSender)
@adapter(IBookingSMSMessage, IPrenotazione, IRedturtlePrenotazioniStagingLayer)
class DemoSMSSenderAdapter(BookingNotificationSender):
    def send(self):
        if self.is_notification_allowed():
            message = self.message_adapter.message
            phone = self.booking.phone
            api.portal.send_email(
                recipient=f"{phone}@redturtle.it",
                subject=f"SMS to {phone}",
                body=message,
            )

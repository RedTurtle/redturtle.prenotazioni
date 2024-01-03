# -*- coding: utf-8 -*-
import os

from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer

from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingAPPIoMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.io_tools.api import Api
from redturtle.prenotazioni.io_tools.storage import logstorage


@implementer(IBookingNotificationSender)
@adapter(IBookingAPPIoMessage, IPrenotazione, IRedturtlePrenotazioniLayer)
class BookingTransitionAPPIoSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self):
        message = self.message_adapter.message
        subject = self.message_adapter.subject
        booking_type = self.booking.get_booking_type()
        service_code = getattr(booking_type, "service_code", None)

        if not service_code:
            return

        api_key = os.environ.get(service_code)

        if not api_key:
            return

        if getUtility(IBookingNotificatorSupervisorUtility).is_appio_message_allowed(
            self.booking
        ):
            api = Api(secret=api_key, storage=logstorage)
            id = api.send_message(
                fiscal_code=self.booking.fiscalcode,
                subject=subject,
                body=message,
            )

            if not id:
                logger.error("Could not send notification via AppIO gateway")
                return

            logger.info(
                f"Sent the notification <{self.booking.UID()}>(`{message}`, `{subject}`) via AppIO gateway, id returned: {id}"
            )

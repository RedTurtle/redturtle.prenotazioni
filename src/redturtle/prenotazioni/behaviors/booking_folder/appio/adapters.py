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


# TODO: ramcache ?
def app_io_allowed_for(fiscalcode, service_code):
    """Check if the user is allowed to receive App IO notifications for the given service code"""
    if not fiscalcode:
        return False

    if not service_code:
        return False

    api_key = os.environ.get(service_code)
    if not api_key:
        logger.warning("No App IO API key found for service code %s", service_code)
        return False

    api = Api(secret=api_key)
    return api.is_service_activated(fiscalcode)


@implementer(IBookingNotificationSender)
@adapter(IBookingAPPIoMessage, IPrenotazione, IRedturtlePrenotazioniLayer)
class BookingTransitionAPPIoSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self) -> bool:
        supervisor = getUtility(IBookingNotificatorSupervisorUtility)
        if supervisor.is_appio_message_allowed(self.booking):
            message = self.message_adapter.message
            subject = self.message_adapter.subject
            booking_type = self.booking.get_booking_type()
            service_code = getattr(booking_type, "service_code", None)

            if not self.booking.fiscalcode:
                logger.warning(
                    "No fiscal code found for booking %s", self.booking.UID()
                )
                return False

            if not service_code:
                logger.warning(
                    "No App IO service code found for booking type %s", booking_type
                )
                return False

            api_key = os.environ.get(service_code)
            if not api_key:
                logger.warning(
                    "No App IO API key found for service code %s booking type %s",
                    service_code,
                    booking_type,
                )
                return False

            api = Api(secret=api_key, storage=logstorage)

            # XXX: qui si usa supervisor perchè nei test c'è un mock su questo
            # if not api.is_service_activated(self.booking.fiscalcode):
            if not supervisor.app_io_allowed_for(self.booking.fiscalcode, service_code):
                logger.info(
                    "App IO service %s is not activated for fiscal code %s",
                    service_code,
                    self.booking.fiscalcode,
                )
                return False

            msgid = api.send_message(
                fiscal_code=self.booking.fiscalcode,
                subject=subject,
                body=message,
            )

            if not msgid:
                logger.error("Could not send notification via AppIO gateway")
                return False

            logger.info(
                "Sent the notification <%s>(`%s`) via AppIO gateway, id returned: %s",
                self.booking.UID(),
                subject,
                msgid,
            )
            return True

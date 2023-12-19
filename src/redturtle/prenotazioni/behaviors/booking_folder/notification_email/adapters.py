# -*- coding: utf-8 -*-
from logging import getLogger

from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.utilities import send_email

logger = getLogger(__name__)


@implementer(IBookingNotificationSender)
@adapter(IBookingEmailMessage, IPrenotazione, IRedturtlePrenotazioniLayer)
class BookingTransitionEmailSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self, force=False):
        message = self.message_adapter.message

        if (
            getUtility(
                IBookingNotificatorSupervisorUtility,
            ).is_email_message_allowed(self.booking)
            or force
        ):
            logger.info(
                f"Sending the notification <{self.booking.UID()}>(`{message}`) via Email gateway"
            )
            send_email(message)

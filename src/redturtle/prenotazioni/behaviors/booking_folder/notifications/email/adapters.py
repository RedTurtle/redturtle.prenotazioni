# -*- coding: utf-8 -*-
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer

from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingEmailMessage
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer
from redturtle.prenotazioni.utilities import send_email

from .. import write_message_to_object_history


@implementer(IBookingNotificationSender)
@adapter(IBookingEmailMessage, IPrenotazione, IRedturtlePrenotazioniLayer)
class BookingTransitionEmailSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self, force=False):
        """
        force: bool
            If True, the message will be sent even if the email is not allowed
            (ie. for operator notifications)
        """

        message = self.message_adapter.message

        if force or getUtility(
            IBookingNotificatorSupervisorUtility
        ).is_email_message_allowed(self.booking):
            logger.debug(
                f"Sending the notification <{self.booking.UID()}>(`{message}`) via Email gateway"
            )
            logger.info(
                f"Sending the notification <{self.booking.UID()}> via Email gateway"
            )

            send_email(message)
            write_message_to_object_history(
                self.booking, message=self.message_adapter.message_history
            )

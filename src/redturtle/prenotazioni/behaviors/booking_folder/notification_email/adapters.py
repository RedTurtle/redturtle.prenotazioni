from logging import getLogger

from zope.component import adapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.utilities import send_email

logger = getLogger(__name__)


@implementer(IBookingNotificationSender)
@adapter(IPrenotazioneEmailMessage, IPrenotazione)
class BookingTransitionEmailSender:
    def __init__(self, message_adapter, booking) -> None:
        self.message_adapter = message_adapter
        self.booking = booking

    def send(self):
        message = self.message_adapter.message

        if getUtility(
            IBookingNotificatorSupervisorUtility,
        ).is_appio_message_allowed(self.booking):
            logger.info(
                f"Sending the notification <{self.booking.UID()}>(`{message}`) via Email gateway"
            )
            send_email(message)

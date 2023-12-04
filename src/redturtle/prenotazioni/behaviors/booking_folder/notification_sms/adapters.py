from logging import getLogger

from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IPrenotazioneSMSMEssage

logger = getLogger(__name__)


@implementer(IBookingNotificationSender)
@adapter(IPrenotazioneSMSMEssage, IPrenotazione)
class BookingNotificationSender:
    def __init__(self, message_adapter, booking) -> None:
        self.message_adapter = message_adapter
        self.booking = booking

    def send(self):
        message = self.message_adapter.message

        logger.info(
            f"Sending the notification <{self.booking.UID()}>(`{message}`) via SMS gateway"
        )

from logging import getLogger

from zope.component import adapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface import Interface

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IBookingNotificatorSupervisorUtility
from redturtle.prenotazioni.interfaces import IPrenotazioneSMSMessage

logger = getLogger(__name__)


@implementer(IBookingNotificationSender)
@adapter(IPrenotazioneSMSMessage, IPrenotazione, Interface)
class BookingNotificationSender:
    def __init__(self, message_adapter, booking, request) -> None:
        self.message_adapter = message_adapter
        self.booking = booking
        self.request = request

    def send(self):
        message = self.message_adapter.message

        if getUtility(
            IBookingNotificatorSupervisorUtility,
        ).is_appio_message_allowed(self.booking):
            return
        logger.info(
            f"Sending the notification <{self.booking.UID()}>(`{message}`) via SMS gateway"
        )

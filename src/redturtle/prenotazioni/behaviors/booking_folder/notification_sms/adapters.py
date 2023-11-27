from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IPrenotazioneSMSMEssage


@implementer(IBookingNotificationSender)
@adapter(IPrenotazioneSMSMEssage, IPrenotazione)
class BookingTransitionSMSSender:
    def __init__(self, message_adapter, booking) -> None:
        self.message_adapter = message_adapter
        self.booking = booking

    @staticmethod
    def send():
        NotImplementedError("The method was not implemented")

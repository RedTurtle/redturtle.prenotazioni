from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingNotificationSender
from redturtle.prenotazioni.interfaces import IPrenotazioneEmailMessage
from redturtle.prenotazioni.utilities import send_email


@implementer(IBookingNotificationSender)
@adapter(IPrenotazioneEmailMessage, IPrenotazione)
class BookingTransitionEmailSender:
    def __init__(self, message_adapter, booking) -> None:
        self.message_adapter = message_adapter
        self.booking = booking

    def send(self):
        send_email(self.message_adapter.message)

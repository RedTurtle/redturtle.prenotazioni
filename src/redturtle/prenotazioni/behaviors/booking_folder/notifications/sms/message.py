# -*- coding: utf-8 -*-
"""SMS Notification Templates"""

from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from redturtle.prenotazioni.interfaces import IBookingSMSMessage
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione


class PrenotazioneSMSMessage:
    prenotazione = None
    event = None

    def __init__(self, prenotazione, event):
        self.prenotazione = prenotazione
        self.event = event

    @property
    def message(self) -> str:
        NotImplementedError


@implementer(IBookingSMSMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedSMSMessage(PrenotazioneSMSMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_on_move_sms_message",
                None,
            ),
        )


@implementer(IBookingSMSMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionSMSMessage(PrenotazioneSMSMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                f"notify_on_{self.event.transition and self.event.transition.__name__}_sms_message",
                None,
            ),
        )


@implementer(IBookingSMSMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneReminderSMSMessage(PrenotazioneSMSMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_reminder_sms_message",
                "",
            )
        )

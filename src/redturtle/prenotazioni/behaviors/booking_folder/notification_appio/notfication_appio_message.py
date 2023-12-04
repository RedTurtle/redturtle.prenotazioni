# -*- coding: utf-8 -*-
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni import _
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from redturtle.prenotazioni.interfaces import IPrenotazioneAPPIoMessage
from redturtle.prenotazioni.prenotazione_event import IMovedPrenotazione


class PrenotazioneAPPIoMessage:
    prenotazione = None
    event = None

    def __init__(self, prenotazione, event):
        self.prenotazione = prenotazione
        self.event = event

    @property
    def message(self) -> str:
        NotImplementedError


@implementer(IPrenotazioneAPPIoMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedAPPIoMessage(PrenotazioneAPPIoMessage):
    @property
    def message(self) -> str:
        return (
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    self.prenotazione.getPrenotazioniFolder(),
                    f"notify_on_move_appio_message",
                    None,
                ),
            ),
        )


@implementer(IPrenotazioneAPPIoMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionAPPIoMessage(PrenotazioneAPPIoMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                f"notify_on_{self.event.transition and self.event.transition.__name__}_appio_message",
                None,
            ),
        )


@implementer(IPrenotazioneAPPIoMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneReminderAppIoMessage(PrenotazioneAPPIoMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_reminder_appio_message",
                "",
            )
        )

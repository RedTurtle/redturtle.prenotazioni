# -*- coding: utf-8 -*-
"""AppIO notification templates"""
from plone import api
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter
from zope.interface import implementer

from redturtle.prenotazioni import _
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingAPPIoMessage
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
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


@implementer(IBookingAPPIoMessage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedAPPIoMessage(PrenotazioneAPPIoMessage):
    @property
    def message_history(self) -> str:
        _(
            "history_appio_reschedule_sent",
            default="AppIO message about the booking reschedule was sent",
        )

    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_on_move_appio_message",
                None,
            )
        )

    @property
    def subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_on_move_appio_subject",
                "",
            )
        )


@implementer(IBookingAPPIoMessage)
@adapter(IPrenotazione, IAfterTransitionEvent)
class PrenotazioneAfterTransitionAPPIoMessage(PrenotazioneAPPIoMessage):
    @property
    def message_history(self) -> str:
        transition = (
            self.event.transition
            and api.portal.translate(self.event.transition.title)
            or ""
        )

        return api.portal.translate(
            _(
                "history_appio_transition_sent",
                "AppIO message about the ${transition} transition was sent.",
                mapping={"transition": transition},
            ),
        )

    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                f"notify_on_{self.event.transition and self.event.transition.__name__}_appio_message",
                None,
            )
        )

    @property
    def subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                f"notify_on_{self.event.transition and self.event.transition.__name__}_appio_subject",
                None,
            )
        )


@implementer(IBookingAPPIoMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneReminderAppIOMessage(PrenotazioneAPPIoMessage):
    @property
    def message_history(self) -> str:
        return api.portal.translate(
            _("history_appio_reminder_sent", default="AppIO reminder was sent")
        )

    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_reminder_appio_message",
                "",
            )
        )

    @property
    def subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_reminder_appio_subject",
                "",
            )
        )


@implementer(IBookingAPPIoMessage)
@adapter(IPrenotazione, IBookingReminderEvent)
class PrenotazioneRemovedAppIOMessage(PrenotazioneAPPIoMessage):
    @property
    def message(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_removed_appio_message",
                "",
            )
        )

    @property
    def subject(self) -> str:
        return IStringInterpolator(IContextWrapper(self.prenotazione)())(
            getattr(
                self.prenotazione.getPrenotazioniFolder(),
                "notify_as_removed_appio_subject",
                "",
            )
        )

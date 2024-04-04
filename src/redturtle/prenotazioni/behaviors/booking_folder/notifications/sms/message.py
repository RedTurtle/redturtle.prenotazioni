# -*- coding: utf-8 -*-
"""SMS Notification Templates"""

from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter
from zope.i18n import translate
from zope.interface import implementer

from redturtle.prenotazioni import _
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
        raise NotImplementedError("The method was not implemented")

    @property
    def message_history(self) -> str:
        raise NotImplementedError("The method was not implemented")


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

    @property
    def message_history(self) -> str:
        return self.prenotazione.translate(
            _("SMS about the booking reschedule was sent")
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

    @property
    def message_history(self) -> str:
        transition = self.event.transition and translate(
            self.event.transition.__name__, context=self.prenotazione
        )
        return self.prenotazione.translate(
            _("SMS about the {transizion} transition was sent")
        ).format(transition=transition)


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

    @property
    def message_history(self) -> str:
        return self.prenotazione.translate(_("SMS reminder was sent"))

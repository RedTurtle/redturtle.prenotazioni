# -*- coding: utf-8 -*-
"""In this module we implemented the booking email templates which were used
    by plone contenttrules in previous verisions of the package"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from plone import api
from plone.app.event.base import default_timezone
from plone.event.interfaces import IICalendar
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringInterpolator
from plone.stringinterp.interfaces import IStringSubstitution
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import getAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.lifecycleevent import IObjectAddedEvent

from redturtle.prenotazioni import _
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.interfaces import IBookingReminderEvent
from redturtle.prenotazioni.interfaces import IPrenotazioneSMSMEssage
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


@implementer(IPrenotazioneSMSMEssage)
@adapter(IPrenotazione, IMovedPrenotazione)
class PrenotazioneMovedSMSMessage(PrenotazioneSMSMessage):
    @property
    def message(self) -> str:
        return (
            IStringInterpolator(IContextWrapper(self.prenotazione)())(
                getattr(
                    self.prenotazione.getPrenotazioniFolder(),
                    f"notify_on_move_sms_message",
                    None,
                ),
            ),
        )


@implementer(IPrenotazioneSMSMEssage)
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


@implementer(IPrenotazioneSMSMEssage)
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

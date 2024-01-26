# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.interface.interfaces import IObjectEvent
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRedturtlePrenotazioniLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IPause(Interface):
    """Marker interface that defines a pause fake type object"""


class ISerializeToPrenotazioneSearchableItem(Interface):
    """Prenotazione searchable item serializer interface"""


class ISerializeToRetroCompatibleJson(Interface):
    """Interface used to cereate the TEMPORARY retrocomattible serializers"""


class IBookingReminderEvent(IObjectEvent):
    """Booking reminder time arrived event"""


class IBookingNotificationSender(Interface):
    """Booking notification sender"""


class IBookingEmailMessage(Interface):
    """Prenotazione email message which is being used by the email gateway"""


class IBookingSMSMessage(Interface):
    """Prenotazione SMS message adapter which is being used by the SMS gateway"""


class IBookingAPPIoMessage(Interface):
    """Prenotazione AppIO message adapter which being used by the App IO gateway"""


class IBookingNotificatorSupervisorUtility(Interface):
    """Bookign notificator supervisor
    basically contains the business logic to allow/disallow the
    notification sending to gateways
    """

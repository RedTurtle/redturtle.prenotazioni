# -*- coding: utf-8 -*-
import icalendar
from Acquisition import aq_inner
from plone.app.event.base import default_timezone
from plone.app.event.ical.exporter import PRODID
from plone.app.event.ical.exporter import VERSION
from plone.app.event.ical.exporter import ICalendarEventComponent
from plone.event.interfaces import IICalendar
from plone.event.interfaces import IICalendarEventComponent
from plone.registry.interfaces import IRegistry
from plone.stringinterp.interfaces import IContextWrapper
from plone.stringinterp.interfaces import IStringSubstitution
from zope.annotation.interfaces import IAnnotations
from zope.component import getAdapter
from zope.component import getUtility
from zope.interface import implementer
from plone import api

from redturtle.prenotazioni import _


def construct_icalendar(context, bookings):
    """Returns an icalendar.Calendar object.

    :param context: A content object, which is used for calendar details like
                    Title and Description. Usually a container, collection or
                    the event itself.

    :param bookings: The list of bookings objects, which are included in this
                   calendar.
    """
    cal = icalendar.Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", VERSION)

    cal_tz = default_timezone(context)
    if cal_tz:
        cal.add("x-wr-timezone", cal_tz)

    if not getattr(bookings, "__getitem__", False):
        bookings = [bookings]
    for booking in bookings:
        cal.add_component(IICalendarEventComponent(booking).to_ical())
    return cal


@implementer(IICalendarEventComponent)
class ICalendarBookingComponent(ICalendarEventComponent):
    def __init__(self, context):
        self.context = context
        self.event = self.context
        self.ical = icalendar.Event()

    @property
    def parent(self):
        return self.context.getPrenotazioniFolder()

    @property
    def dtstart(self):
        return {"value": self.context.booking_date}

    @property
    def dtend(self):
        return {"value": self.context.booking_expiration_date}

    @property
    def summary(self):
        # XXX: `self.context.translate` raise Unauthorized exception
        # Module Products.PythonScripts.PythonScript, line 338, in _exec
        # Module script, line 19, in translate
        # <FSPythonScript at /Plone/cartella-prenotazioni/2023/37/1//translate>
        # Line 19
        # Module Products.CMFPlone.TranslationServiceTool, line 47, in translate
        # Module Shared.DC.Scripts.Bindings, line 199, in __getattr__
        # Module Shared.DC.Scripts.Bindings, line 205, in __you_lose
        # AccessControl.unauthorized.Unauthorized: <exception str() failed>
        annotations = IAnnotations(self.context.REQUEST)

        is_manager_notification = annotations.get("ical_manager_notification", False)
        title_label = self.parent.title
        if is_manager_notification:
            title_label = f"{self.context.title} [{title_label}]"
        title = api.portal.translate(
            _(
                "ical_booking_label",
                default="Booking for ${title}",
                mapping={"title": title_label},
            )
        )
        return {"value": title}

    @property
    def url(self):
        return {
            "value": getAdapter(
                IContextWrapper(self.context),
                IStringSubstitution,
                "booking_print_url",
            )()
        }

    @property
    def location(self):
        return {"value": getattr(self.parent, "complete_address", "")}

    @property
    def contact(self):
        email = getattr(self.parent, "pec", "")
        if not email:
            registry = getUtility(IRegistry)
            record = registry.records.get("plone.email_from_address", None)
            if record:
                email = record.value
        return {"value": email}

    @property
    def uid(self):
        return {"value": self.context.UID()}

    @property
    def organizer(self):
        return {
            "value": "MAILTO:{}".format(self.contact.get("value", "")),
            "parameters": {"CN": self.parent.title},
        }

    def to_ical(self):
        # TODO: event.text
        ical_add = self.ical_add
        ical_add("dtstamp", self.dtstamp)
        ical_add("created", self.created)
        ical_add("last-modified", self.last_modified)
        ical_add("uid", self.uid)
        ical_add("url", self.url)
        ical_add("summary", self.summary)
        ical_add("description", self.description)
        ical_add("dtstart", self.dtstart)
        ical_add("dtend", self.dtend)
        ical_add("location", self.location)
        ical_add("contact", self.contact)
        ical_add("organizer", self.organizer)
        return self.ical


@implementer(IICalendar)
def calendar_from_booking(context):
    """Booking adapter. Returns an icalendar.Calendar object from a Booking
    context.
    """
    context = aq_inner(context)
    return construct_icalendar(context, [context])

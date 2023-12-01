# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from logging import getLogger

from plone import api
from Products.Five.browser import BrowserView
from zope.event import notify

from redturtle.prenotazioni.events import BookingReminderEvent

logger = getLogger(__name__)


class NotifyUpcomingBookings(BrowserView):
    """View to notify about the upcoming bookings"""

    def __call__(self):
        today = datetime.now().replace(hour=0, minute=0)
        unrestricted_search = api.portal.get_tool(
            "portal_catalog"
        ).unrestrictedSearchResults

        for brain in unrestricted_search(portal_type="PrenotazioniFolder"):
            booking_folder = brain.getObject()
            reminder_notification_gap = getattr(
                booking_folder, "reminder_notification_gap", None
            )

            if not reminder_notification_gap:
                logger.info(
                    f"No notification gap was found for the <{brain.getPath()}>"
                )
                continue

            for booking in unrestricted_search(
                portal_type="Prenotazione",
                path=brain.getPath(),
                Date={
                    "query": (
                        today + timedelta(days=reminder_notification_gap),
                        today
                        + timedelta(
                            days=reminder_notification_gap, hours=23, minutes=59
                        ),
                    ),
                    "range": "min:max",
                },
                review_state="confirmed",
            ):
                notify(BookingReminderEvent(booking.getObject()))
                logger.info(f"A reminder to {booking.getPath()} has been sent")

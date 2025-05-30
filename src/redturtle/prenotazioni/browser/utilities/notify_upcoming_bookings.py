# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from plone import api
from Products.Five.browser import BrowserView
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.events import BookingReminderEvent
from zope.event import notify


class NotifyUpcomingBookings(BrowserView):
    """View to notify about the upcomming bookings"""

    def __call__(self):
        today = datetime.now().replace(hour=0, minute=0)
        catalog = api.portal.get_tool("portal_catalog")

        for brain in catalog.unrestrictedSearchResults(
            portal_type="PrenotazioniFolder", review_state="published"
        ):
            booking_folder = brain.getObject()
            reminder_notification_gap = getattr(
                booking_folder, "reminder_notification_gap", None
            )

            if not reminder_notification_gap:
                logger.info(
                    f"No notification gap was found for the <{brain.getPath()}>"
                )
                continue

            for booking in catalog.unrestrictedSearchResults(
                portal_type="Prenotazione",
                path=brain.getPath(),
                Date={
                    "query": (
                        today + timedelta(days=reminder_notification_gap),
                        today
                        + timedelta(
                            days=reminder_notification_gap,
                            hours=23,
                            minutes=59,
                            seconds=59,
                        ),
                    ),
                    "range": "min:max",
                },
                review_state="confirmed",
            ):
                notify(BookingReminderEvent(booking.getObject()))
                logger.info(f"A reminder to {booking.getPath()} has been sent")

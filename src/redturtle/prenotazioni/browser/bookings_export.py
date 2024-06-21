# -*- coding: utf-8 -*-
import csv
import datetime

from plone import api
from Products.Five import BrowserView
from six import StringIO
from zExceptions import BadRequest

from redturtle.prenotazioni import _
from redturtle.prenotazioni.restapi.serializers.adapters.prenotazione import (
    get_booking_wf_state_title,
)
from redturtle.prenotazioni.utilities.dateutils import get_default_timezone


class BookingsExport(BrowserView):
    filename = "Bookings_export"
    date = None

    @property
    def csv_fields(self):
        return [
            api.portal.translate(_("csv_export_uid", default="UID")),
            api.portal.translate(_("csv_export_code", default="CODE")),
            api.portal.translate(_("csv_export_type", default="TYPE")),
            api.portal.translate(_("csv_export_phone", default="PHONE")),
            api.portal.translate(_("csv_export_email", default="EMAIL")),
            api.portal.translate(_("csv_export_name", default="NAME SURNAME")),
            api.portal.translate(_("csv_export_fiscalcode", default="FISCALCODE")),
            api.portal.translate(_("csv_export_start_time", default="BOOKING START")),
            api.portal.translate(
                _("csv_export_end_time", default="BOOKING EXPIRATION")
            ),
            api.portal.translate(_("csv_export_state", default="STATE")),
            api.portal.translate(_("csv_export_gate", default="GATE")),
            api.portal.translate(_("csv_export_notes", default="NOTES")),
            api.portal.translate(
                _("csv_export_booking_folder", default="BOOKING FOLDER")
            ),
            api.portal.translate(_("csv_export_company", default="COMPANY")),
        ]

    @property
    def csv_filename(self):
        """Return a filename for this csv"""

        return "%s-%s.csv" % (self.filename, self.date.date().isoformat())

    @property
    def brains(self):

        return api.portal.get_tool("portal_catalog").unrestrictedSearchResults(
            portal_type="Prenotazione",
            Date={
                "query": (
                    get_default_timezone(True).localize(self.date),
                    get_default_timezone(True).localize(
                        self.date.replace(hour=23, minute=59)
                    ),
                ),
                "range": "min:max",
            },
            review_state="confirmed",
            sort_on="Date",
        )

    def setHeader(self, *args):
        """
        Shorcut for setting headers in the request
        """
        return self.context.REQUEST.RESPONSE.setHeader(*args)

    def brain2row(self, brain):
        """
        returns a generator with the booking data
        """
        booking = brain.getObject()

        return {
            api.portal.translate(_("csv_export_uid", default="UID")): booking.UID(),
            api.portal.translate(
                _("csv_export_code", default="CODE")
            ): booking.getBookingCode(),
            api.portal.translate(
                _("csv_export_type", default="TYPE")
            ): booking.booking_type,
            api.portal.translate(_("csv_export_phone", default="PHONE")): booking.phone,
            api.portal.translate(_("csv_export_email", default="EMAIL")): booking.email,
            api.portal.translate(
                _("csv_export_fiscalcode", default="FISCALCODE")
            ): getattr(booking, "fiscalcode", "").upper(),
            api.portal.translate(
                _("csv_export_start_time", default="BOOKING START")
            ): booking.booking_date.strftime("%Y-%m-%d %H:%M"),
            api.portal.translate(
                _("csv_export_end_time", default="BOOKING EXPIRATION")
            ): booking.booking_expiration_date.strftime("%Y-%m-%d %H:%M"),
            api.portal.translate(
                _("csv_export_notes", default="NOTES")
            ): booking.description,
            api.portal.translate(
                _("csv_export_state", default="STATE")
            ): get_booking_wf_state_title(booking),
            api.portal.translate(_("csv_export_gate", default="GATE")): booking.gate,
            api.portal.translate(
                _("csv_export_booking_folder", default="BOOKING FOLDER")
            ): booking.getPrenotazioniFolder().Title(),
            api.portal.translate(
                _("csv_export_company", default="COMPANY")
            ): booking.company,
            api.portal.translate(
                _("csv_export_name", default="NAME SURNAME")
            ): booking.title,
        }

    def get_csv_rows(self):
        """Return the csv rows as a dictionary"""
        for brain in self.brains:
            yield self.brain2row(brain)

    def get_csv(self):
        """Get a csv out of the view brains"""

        buffer = StringIO()
        csv_writer = csv.DictWriter(buffer, fieldnames=self.csv_fields)

        csv_writer.writeheader()

        for row in self.get_csv_rows():
            csv_writer.writerow(row)

        buffer.seek(0)

        return buffer.getvalue().encode("utf-8")

    def __call__(self):
        date = self.request.get("date")

        if not date:
            self.date = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.min.time()
            )
        else:
            try:
                self.date = datetime.datetime.combine(
                    datetime.date.fromisoformat(date), datetime.datetime.min.time()
                )
            except ValueError:
                raise BadRequest(_("Bad date format passed"))
        self.setHeader(
            "Content-Disposition", "attachment;filename=%s" % self.csv_filename
        )
        self.request.response.setHeader(
            "Content-Type",
            "application/csv",
        )

        return self.get_csv()

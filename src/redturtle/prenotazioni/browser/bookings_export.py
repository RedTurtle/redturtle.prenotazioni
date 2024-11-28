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
    booking_start_from = None
    booking_start_to = None
    booking_creation_from = None
    booking_creation_to = None
    path = None

    @property
    def csv_fields(self):
        return [
            api.portal.translate(_("csv_export_uid", default="UID")),
            api.portal.translate(_("csv_export_creator", default="CREATOR")),
            api.portal.translate(
                _("csv_export_creation_date", default="CREATION DATE")
            ),
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

        return self.filename + ".csv"

    @property
    def brains(self):
        created = (self.booking_creation_from or self.booking_creation_to) and {
            "query": (self.booking_creation_from and self.booking_creation_to)
            and (
                get_default_timezone(True).localize(self.booking_creation_from),
                get_default_timezone(True).localize(self.booking_creation_to),
            )
            or self.booking_creation_from
            and get_default_timezone(True).localize(self.booking_creation_from)
            or self.booking_creation_to
            and get_default_timezone(True).localize(self.booking_creation_to),
            "range": (self.booking_creation_from and self.booking_creation_to)
            and "min:max"
            or self.booking_creation_from
            and "min"
            or self.booking_creation_to
            and "max",
        }

        date = (self.booking_start_from or self.booking_start_to) and {
            "query": (self.booking_start_from and self.booking_start_to)
            and (
                get_default_timezone(True).localize(self.booking_start_from),
                get_default_timezone(True).localize(self.booking_start_to),
            )
            or self.booking_start_from
            and get_default_timezone(True).localize(self.booking_start_from)
            or self.booking_start_to
            and get_default_timezone(True).localize(self.booking_start_to),
            "range": (self.booking_start_from and self.booking_start_to)
            and "min:max"
            or self.booking_start_from
            and "min"
            or self.booking_start_to
            and "max",
        }

        query = dict(
            portal_type="Prenotazione",
            review_state="confirmed",
            sort_on="Date",
        )

        if created:
            query["created"] = created

        if date:
            query["Date"] = date

        if self.path:
            query["path"] = self.path

        return api.portal.get_tool("portal_catalog").unrestrictedSearchResults(**query)

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
                _("csv_export_creator", default="CREATOR")
            ): booking.Creator(),
            api.portal.translate(
                _("csv_export_creation_date", default="CREATION DATE")
            ): booking.created().strftime("%Y-%m-%d %H:%M:%S"),
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
        booking_start_from = self.request.get("booking_start_from")
        booking_start_to = self.request.get("booking_start_to")
        booking_creation_from = self.request.get("booking_creation_from")
        booking_creation_to = self.request.get("booking_creation_to")
        self.path = self.request.get("booking_folder_path")

        if booking_start_from:
            try:
                self.booking_start_from = datetime.datetime.fromisoformat(
                    booking_start_from
                )
            except ValueError:
                raise BadRequest(
                    api.portal.translate(_("Badly composed `booking_start_from` value"))
                )

        if booking_start_to:
            try:
                self.booking_start_to = datetime.datetime.fromisoformat(
                    booking_start_to
                )
            except ValueError:
                raise BadRequest(
                    api.portal.translate(_("Badly composed `booking_start_to` value"))
                )

        if booking_creation_from:
            try:
                self.booking_creation_from = datetime.datetime.fromisoformat(
                    booking_creation_from
                )
            except ValueError:
                raise BadRequest(
                    api.portal.translate(
                        _("Badly composed `booking_creation_from` value")
                    )
                )

        if booking_creation_to:
            try:
                self.booking_creation_to = datetime.datetime.fromisoformat(
                    booking_creation_to
                )
            except ValueError:
                raise BadRequest(
                    api.portal.translate(
                        _("Badly composed `booking_creation_to` value")
                    )
                )

        self.setHeader(
            "Content-Disposition", "attachment;filename=%s" % self.csv_filename
        )
        self.request.response.setHeader(
            "Content-Type",
            "application/csv",
        )

        return self.get_csv()

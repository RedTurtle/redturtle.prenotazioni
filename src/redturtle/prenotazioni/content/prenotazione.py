# -*- coding: utf-8 -*-
from .prenotazioni_folder import IPrenotazioniFolder
from datetime import datetime
from DateTime import DateTime
from plone import api
from plone.dexterity.content import Item
from plone.supermodel import model
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from zope import schema
from zope.interface import implementer
from zope.schema import ValidationError

import hashlib
import re
import six


TELEPHONE_PATTERN = re.compile(r"^(\+){0,1}([0-9]| )*$")


class InvalidPhone(ValidationError):
    __doc__ = _("invalid_phone_number", "Invalid phone number")


class InvalidEmailAddress(ValidationError):
    __doc__ = _("invalid_email_address", "Invalid email address")


class IsNotfutureDate(ValidationError):
    __doc__ = _("is_not_future_date", "This date is past")


class InvalidFiscalcode(ValidationError):
    __doc__ = _("invalid_fiscalcode", "Invalid fiscal code")


def check_phone_number(value):
    """
    If value exist it should match TELEPHONE_PATTERN
    """
    if not value:
        return True
    if isinstance(value, six.string_types):
        value = value.strip()
    if TELEPHONE_PATTERN.match(value) is not None:
        return True
    raise InvalidPhone(value)


def check_valid_email(value):
    """Check if value is a valid email address"""
    if not value:
        return True
    reg_tool = api.portal.get_tool(name="portal_registration")
    if value and reg_tool.isValidEmail(value):
        return True
    else:
        raise InvalidEmailAddress


def check_valid_fiscalcode(value):
    # fiscal code development
    if value == "AAAAAA00A00A000A":
        return True
    if not value:
        return True
    value = value.upper()
    if not len(value) == 16:
        raise InvalidFiscalcode(value)

    validi = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for c in value:
        if c not in validi:
            raise InvalidFiscalcode(value)

    set1 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    set2 = "ABCDEFGHIJABCDEFGHIJKLMNOPQRSTUVWXYZ"
    setpari = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    setdisp = "BAKPLCQDREVOSFTGUHMINJWZYX"
    s = 0

    for i in range(1, 14, 2):
        s += setpari.find(set2[set1.find(value[i])])
    for i in range(0, 15, 2):
        s += setdisp.find(set2[set1.find(value[i])])

    if s % 26 != (ord(value[15]) - ord("A"[0])):
        raise InvalidFiscalcode(value)

    return True


def check_is_future_date(value):
    """
    Check if this date is in the future
    """
    if not value:
        return True

    now = tznow()

    if isinstance(value, datetime) and value >= now:
        return True
    raise IsNotfutureDate


class IPrenotazione(model.Schema):
    """Marker interface and Dexterity Python Schema for Prenotazione"""

    booking_date = schema.Datetime(
        title=_("label_booking_time", "Booking time"),
        required=True,
        default=None,
        constraint=check_is_future_date,
    )

    booking_type = schema.Choice(
        title=_("label_booking_type", default="Booking type"),
        vocabulary="redturtle.prenotazioni.booking_types",
        required=True,
    )

    email = schema.TextLine(
        title=_("label_booking_email", default="Email"),
        constraint=check_valid_email,
        default="",
        required=False,
    )

    phone = schema.TextLine(
        title=_("label_booking_phone", default="Phone number"),
        required=False,
        default="",
        constraint=check_phone_number,
    )

    fiscalcode = schema.TextLine(
        title=_("label_booking_fiscalcode", default="Fiscal code"),
        default="",
        # constraint=check_valid_fiscalcode,
        required=False,
    )

    company = schema.TextLine(
        title=_("label_booking_company", default="Company"),
        description=_(
            "description_company",
            default="If you work for a company, please specify its name.",
        ),
        required=False,
    )

    gate = schema.TextLine(
        title=_("Gate"),
        description=_("Sportello a cui presentarsi"),
    )

    booking_expiration_date = schema.Datetime(
        title=_("Expiration date booking"), required=True
    )

    staff_notes = schema.Text(
        required=False, title=_("label_booking_staff_notes", "Staff notes")
    )


@implementer(IPrenotazione)
class Prenotazione(Item):
    """ """

    def getBooking_date(self):
        return self.booking_date

    def setBooking_date(self, date):
        self.booking_date = date
        return

    def getBooking_expiration_date(self):
        return self.booking_expiration_date

    def setBooking_expiration_date(self, date):
        self.booking_expiration_date = date
        return

    def getBooking_type(self):
        return self.booking_type

    def getCompany(self):
        return self.company

    def getFiscalcode(self):
        return self.fiscalcode

    def getPhone(self):
        return self.phone

    def getEmail(self):
        return self.email

    def getStaff_notes(self):
        return self.staff_notes

    def getPrenotazioniFolder(self):
        """Ritorna l'oggetto prenotazioni folder"""

        for parent in self.aq_chain:
            if IPrenotazioniFolder.providedBy(parent):
                return parent
        raise Exception(
            "Could not find Prenotazioni Folder " "in acquisition chain of %r" % self
        )

    def getDuration(self):
        """Return current duration"""
        start = self.getBooking_date()
        end = self.getBooking_expiration_date()
        if start and end:
            return end - start
        else:
            return 1

    def Subject(self):
        """Reuse plone subject to do something useful"""
        return ""

    def Date(self):
        """
        Dublin Core element - default date
        """
        # Return reservation date
        return DateTime(self.getBooking_date())

    def getBookingCode(self):
        date = self.booking_date.isoformat()
        hash_obj = hashlib.blake2b(bytes(date, encoding="utf8"), digest_size=3)
        return hash_obj.hexdigest().upper()

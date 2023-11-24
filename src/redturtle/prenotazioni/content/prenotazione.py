# -*- coding: utf-8 -*-
import re

import six
from DateTime import DateTime
from plone import api
from plone.app.event.base import default_timezone
from plone.app.z3cform.widget import DatetimeFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from zope.schema import ValidationError

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni import is_migration
from redturtle.prenotazioni import tznow

from .prenotazioni_folder import IPrenotazioniFolder

VACATION_TYPE = "out-of-office"
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


# TODO: validare considerando anche TINIT-XXX...
# (vedi https://it.wikipedia.org/wiki/Codice_fiscale#Codice_fiscale_ordinario)
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

    # Do not check the value if we are performing a migration
    if is_migration():
        return True

    if not value:
        return True
    try:
        if datetime_with_tz(value) >= tznow():
            return True
        else:
            raise IsNotfutureDate
    except Exception:
        raise IsNotfutureDate


class IPrenotazione(model.Schema):
    """Marker interface and Dexterity Python Schema for Prenotazione"""

    directives.mode(booking_date="display")
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

    directives.mode(gate="display")
    gate = schema.TextLine(
        title=_("Gate"),
        description=_("Sportello a cui presentarsi"),
    )
    directives.mode(booking_expiration_date="display")
    booking_expiration_date = schema.Datetime(
        title=_("Expiration date booking"), required=True
    )

    directives.mode(booking_code="display")
    booking_code = schema.TextLine(
        title=_("label_booking_code", default="Booking code"),
        description=_("description_booking_code", default="Unique booking code"),
        required=False,
    )

    staff_notes = schema.Text(
        required=False, title=_("label_booking_staff_notes", "Staff notes")
    )

    directives.widget(
        "booking_date",
        DatetimeFieldWidget,
        default_timezone=default_timezone,
        klass="booking_date",
    )


@implementer(IPrenotazione)
class Prenotazione(Item):
    """ """

    def isVacation(self):
        self.getBooking_type() == VACATION_TYPE

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
        return self.booking_code

    def canAccessBooking(self):
        return True
        # creator = self.Creator()
        # if api.user.is_anonymous():
        #     if creator:
        #         return False
        # else:
        #     current_user = api.user.get_current()
        #     if (
        #         not api.user.has_permission("redturtle.prenotazioni.ManagePrenotazioni")
        #         and creator != current_user.getUserName()
        #     ):
        #         return False
        # return True

    def canDeleteBooking(self):
        return True
        # creator = self.Creator()
        # if not creator:
        #     if api.user.is_anonymous():
        #         return True
        #     if api.user.has_permission("redturtle.prenotazioni.ManagePrenotazioni"):
        #         return True
        # else:
        #     if api.user.is_anonymous():
        #         return False
        #     current_user = api.user.get_current()
        #     if (
        #         api.user.has_permission("redturtle.prenotazioni.ManagePrenotazioni")
        #         or creator == current_user.getUserName()
        #     ):
        #         return True
        # return False

    def get_booking_type(self):
        return {
            i.title: i for i in self.getPrenotazioniFolder().get_booking_types()
        }.get(self.booking_type, None)

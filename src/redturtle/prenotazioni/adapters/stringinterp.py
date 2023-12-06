# -*- coding: utf-8 -*-
from plone import api
from plone.app.event.base import default_timezone
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.stringinterp.adapters import BaseSubstitution
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import Interface

from redturtle.prenotazioni import _
from redturtle.prenotazioni import logger

try:
    from plone.app.event.base import spell_date

    have_spell_date = True
except ImportError:
    have_spell_date = False
    logger.exception(
        "\n\nImpossibile importare spell_date da plone.app.event; non si potrà"
        " usare ${booking_human_readable_start} nel markup content rules\n\n"
    )


@adapter(Interface)
class GateSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The gate booked.")

    def safe_call(self):
        return getattr(self.context, "gate", "")


@adapter(Interface)
class BookingDateSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booked date.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "booking_date", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date)


@adapter(Interface)
class BookingEndDateSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booked end date.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "booking_expiration_date", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date)


@adapter(Interface)
class BookingTimeSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booked time.")

    def safe_call(self):
        date = getattr(self.context, "booking_date", "")
        if not date:
            return ""
        return date.astimezone(default_timezone(as_tzinfo=True)).strftime("%H:%M")


@adapter(Interface)
class BookingTimeEndSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking time end.")

    def safe_call(self):
        date = getattr(self.context, "booking_expiration_date", "")
        if not date:
            return ""
        return date.astimezone(default_timezone(as_tzinfo=True)).strftime("%H:%M")


@adapter(Interface)
class PrenotazioneTypeSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking type.")

    def safe_call(self):
        return getattr(self.context, "booking_type", "")


@adapter(Interface)
class BookingCodeSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking code.")

    def safe_call(self):
        code = self.context.getBookingCode()
        if not code:
            return ""
        return code


@adapter(Interface)
class BookingUrlSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking print url.")

    def safe_call(self):
        return "{folder}/@@prenotazione_print?uid={uid}".format(
            folder=self.context.getPrenotazioniFolder().absolute_url(),
            uid=self.context.UID(),
        )


@adapter(Interface)
class BookingPrintUrlWithDeleteTokenSubstitution(BookingUrlSubstitution):
    """
    This is a backward compatibility with old version with token
    """

    category = _("Booking")
    description = _("[DEPRECATED] The booking print url with delete token.")


@adapter(Interface)
class BookingUserPhoneSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The phone number of the user who made the reservation.")

    def safe_call(self):
        return getattr(self.context, "phone", "")


@adapter(Interface)
class BookingUserEmailSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The email address of the user who made the reservation.")

    def safe_call(self):
        return getattr(self.context, "email", "")


@adapter(Interface)
class BookingUserDetailsSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The email address of the user who made the reservation.")

    def safe_call(self):
        return getattr(self.context, "description", "")


@adapter(Interface)
class BookingOfficeContactPhoneSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking office contact phone.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "phone", "")


@adapter(Interface)
class BookingOfficeContactPecSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking office contact pec address.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "pec", "")


@adapter(Interface)
class BookingOfficeContactFaxSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking office contact fax.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "fax", "")


@adapter(Interface)
class BookingHowToGetToOfficeSubsitution(BaseSubstitution):
    category = _("Booking")
    description = _(
        "The information to reach the office where user book a" " reservation"
    )

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "how_to_get_here", "")


@adapter(Interface)
class BookingOfficeCompleteAddressSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _(
        "The complete address information of the office where" "user book a reservation"
    )

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "complete_address", "")


@adapter(Interface)
class BookingHRDateStartSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking human readable date")

    def safe_call(self):
        # we need something like martedì 8 settembre 2020 alle ore 11:15

        date = getattr(self.context, "booking_date", "")
        if not date:
            return ""

        if not have_spell_date:
            return "SPELL_DATE_NOT_AVAILABLE"

        info = spell_date(self.context.booking_date, self.context)
        day = "{day_name} {day_number} {month_name} {year} alle ore {hour}:{minute}".format(  # noqa
            day_name=info["wkday_name"],
            day_number=info["day"],
            month_name=info["month_name"],
            year=info["year"],
            hour=info["hour"],
            minute=info["minute2"],
        )
        return day


@adapter(Interface)
class BookingUrlWithDeleteToken(BaseSubstitution):
    category = _("Booking")
    description = _("The booking url with delete token")

    def safe_call(self):
        return "{booking_url}/@@delete_reservation?uid={uid}".format(
            booking_url=self.context.getPrenotazioniFolder().absolute_url(),
            uid=self.context.UID(),
        )


@adapter(Interface)
class BookingOperatorUrlSubstitution(BaseSubstitution):
    category = _("Booking")
    description = _("The booking operator url")

    def safe_call(self):
        return self.context.absolute_url()


@adapter(Interface)
class BookingRefuseMessage(BaseSubstitution):
    category = _("Booking")
    description = _("The booking refuse message")

    def safe_call(self):
        content_history_viewlet = ContentHistoryViewlet(
            self.context, getRequest(), None, None
        )
        site_url = api.portal.get().absolute_url()
        content_history_viewlet.navigation_root_url = site_url
        content_history_viewlet.site_url = site_url
        history = content_history_viewlet.workflowHistory()

        refuse_history = [i for i in history if i.get("action", "") == "refuse"]

        refuse_message = refuse_history and refuse_history[0].get("comments") or ""

        return refuse_message


@adapter(Interface)
class BookingRequirements(BaseSubstitution):
    category = _("Booking")
    description = _("The booking requirements url")

    def safe_call(self):
        requirements = self.context.get_booking_type().requirements

        return requirements and requirements.output or ""


@adapter(Interface)
class PrenotazioniFolderTitle(BaseSubstitution):
    category = _("Booking")
    description = _("The booking folder title")

    def safe_call(self):
        return getattr(self.context.getPrenotazioniFolder(), "title", "")

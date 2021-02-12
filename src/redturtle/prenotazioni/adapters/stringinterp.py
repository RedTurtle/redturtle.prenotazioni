# -*- coding: utf-8 -*-
from plone.stringinterp.adapters import BaseSubstitution
from redturtle.prenotazioni import _
from zope.component import adapter
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from redturtle.prenotazioni.config import DELETE_TOKEN_KEY

try:
    from plone.app.event.base import spell_date

    have_spell_date = True
except ImportError:
    from redturtle.prenotazioni import prenotazioniLogger as logger

    have_spell_date = False
    logger.exception(
        "\n\nImpossibile importare spell_date da plone.app.event; non si potrà"
        " usare ${booking_human_readable_start} nel markup content rules\n\n"
    )


@adapter(Interface)
class GateSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The gate booked.")

    def safe_call(self):
        return getattr(self.context, "gate", "")


@adapter(Interface)
class BookingDateSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booked date.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_prenotazione", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date)


@adapter(Interface)
class BookingEndDateSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booked end date.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_scadenza", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date)


@adapter(Interface)
class BookingTimeSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booked time.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_prenotazione", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date, time_only=True)


@adapter(Interface)
class BookingTimeEndSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking time end.")

    def safe_call(self):
        plone = self.context.restrictedTraverse("@@plone")
        date = getattr(self.context, "data_scadenza", "")
        if not date:
            return ""
        return plone.toLocalizedTime(date, time_only=True)


@adapter(Interface)
class BookingTypeSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking type.")

    def safe_call(self):
        return getattr(self.context, "tipologia_prenotazione", "")


@adapter(Interface)
class BookingCodeSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking code.")

    def safe_call(self):
        code = self.context.getBookingCode()
        if not code:
            return ""
        return code


@adapter(Interface)
class BookingUrlSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking print url.")

    def safe_call(self):
        return "{folder}/@@prenotazione_print?uid={uid}".format(
            folder=self.context.getPrenotazioniFolder().absolute_url(),
            uid=self.context.UID(),
        )


@adapter(Interface)
class BookingPrintUrlWithDeleteTokenSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking print url with delete token.")

    def safe_call(self):
        annotations = IAnnotations(self.context)
        token = annotations.get(DELETE_TOKEN_KEY, None)
        if not token:
            return ""
        return "{folder}/@@prenotazione_print?uid={uid}&{delete_token_key}={token}".format(  # noqa
            folder=self.context.getPrenotazioniFolder().absolute_url(),
            uid=self.context.UID(),
            delete_token_key=DELETE_TOKEN_KEY,
            token=token,
        )


@adapter(Interface)
class BookingUserPhoneSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The phone number of the user who made the reservation.")

    def safe_call(self):
        return getattr(self.context, "phone", "")


@adapter(Interface)
class BookingUserEmailSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The email address of the user who made the reservation.")

    def safe_call(self):
        return getattr(self.context, "email", "")


@adapter(Interface)
class BookingOfficeContactPhoneSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking office contact phone.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "phone", "")


@adapter(Interface)
class BookingOfficeContactPecSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking office contact pec address.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "pec", "")


@adapter(Interface)
class BookingOfficeContactFaxSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking office contact fax.")

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "fax", "")


@adapter(Interface)
class BookingHowToGetToOfficeSubsitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(
        u"The information to reach the office where user book a" " reservation"
    )

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "how_to_get_here", "")


@adapter(Interface)
class BookingOfficeCompleteAddressSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(
        u"The complete address information of the office where"
        "user book a reservation"
    )

    def safe_call(self):
        prenotazioni_folder = self.context.getPrenotazioniFolder()
        return getattr(prenotazioni_folder, "complete_address", "")


@adapter(Interface)
class BookingHRDateStartSubstitution(BaseSubstitution):

    category = _(u"Booking")
    description = _(u"The booking human readable date")

    def safe_call(self):
        # we need something like martedì 8 settembre 2020 alle ore 11:15

        date = getattr(self.context, "data_prenotazione", "")
        if not date:
            return ""

        if not have_spell_date:
            return "SPELL_DATE_NOT_AVAILABLE"

        info = spell_date(self.context.data_prenotazione, self.context)
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

    category = _(u"Booking")
    description = _(u"The booking url with delete token")

    def safe_call(self):
        annotations = IAnnotations(self.context)
        token = annotations.get(DELETE_TOKEN_KEY, None)
        if not token:
            return ""

        return "{booking_url}/@@delete_reservation?uid={uid}&{delete_token_key}={token}".format(
            booking_url=self.context.getPrenotazioniFolder().absolute_url(),
            delete_token_key=DELETE_TOKEN_KEY,
            uid=self.context.UID(),
            token=token,
        )

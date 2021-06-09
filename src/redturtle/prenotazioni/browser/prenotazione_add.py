# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from datetime import datetime
from DateTime import DateTime
from datetime import timedelta
from email.utils import formataddr
from email.utils import parseaddr
from os import environ
from plone import api
from plone.formwidget.recaptcha.widget import ReCaptchaFieldWidget
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from plone.z3cform.layout import wrap_form
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.browser.z3c_custom_widget import (
    CustomRadioFieldWidget,
)
from redturtle.prenotazioni.utilities.urls import urlify
from six.moves.urllib.parse import urlparse, parse_qs
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import ActionExecutionError
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import Choice
from zope.schema import Datetime
from zope.schema import Text
from zope.schema import TextLine
from zope.schema import ValidationError
from zope.annotation.interfaces import IAnnotations
from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from zope.schema.interfaces import IVocabularyFactory
import re
import six


TELEPHONE_PATTERN = re.compile(r"^(\+){0,1}([0-9]| )*$")


class InvalidPhone(ValidationError):
    __doc__ = _("invalid_phone_number", u"Invalid phone number")


class InvalidEmailAddress(ValidationError):
    __doc__ = _("invalid_email_address", u"Invalid email address")


class IsNotfutureDate(ValidationError):
    __doc__ = _("is_not_future_date", u"This date is past")


class InvalidFiscalcode(ValidationError):
    __doc__ = _("invalid_fiscalcode", u"Invalid fiscal code")


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
    portal = getUtility(ISiteRoot)

    reg_tool = getToolByName(portal, "portal_registration")
    if value and reg_tool.isValidEmail(value):
        return True
    else:
        raise InvalidEmailAddress


def check_valid_fiscalcode(value):
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


class IAddForm(Interface):

    """
    Interface for creating a prenotazione
    """

    booking_date = Datetime(
        title=_("label_booking_time", u"Booking time"),
        default=None,
        constraint=check_is_future_date,
    )
    tipology = Choice(
        title=_("label_typology", u"Typology"),
        required=False,
        default=u"",
        vocabulary="redturtle.prenotazioni.tipologies",
    )
    fullname = TextLine(
        title=_("label_fullname", u"Fullname"), default=u"", required=False
    )
    email = TextLine(
        title=_("label_email", u"Email"),
        required=False,
        default=u"",
        constraint=check_valid_email,
    )
    phone = TextLine(
        title=_("label_phone", u"Phone number"),
        required=False,
        default=u"",
        constraint=check_phone_number,
    )

    fiscalcode = TextLine(
        title=_("label_fiscalcode", u"Fiscal code"),
        required=False,
        default=u"",
        constraint=check_valid_fiscalcode,
    )

    agency = TextLine(
        title=_("label_agency", u"Agency"),
        description=_(
            "description_agency",
            u"If you work for an agency please specify its name",
        ),
        default=u"",
        required=False,
    )

    subject = Text(
        title=_("label_subject", u"Subject"), default=u"", required=False
    )

    captcha = TextLine(title=u" ", description=u"", required=False)


@implementer(IAddForm)
class AddForm(form.AddForm):
    """
    """

    render_form = False
    ignoreContext = True

    @property
    def fields(self):
        fields = field.Fields(IAddForm)
        fields["captcha"].widgetFactory = ReCaptchaFieldWidget
        fields["tipology"].widgetFactory = CustomRadioFieldWidget
        if api.user.is_anonymous():
            return fields
        return fields.omit("captcha")

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets["booking_date"].mode = HIDDEN_MODE
        bookingdate = self.request.form.get(
            "form.booking_date",
            self.request.form.get("form.widgets.booking_date"),
        )
        self.widgets["booking_date"].value = bookingdate
        required_fields_factory = getUtility(
            IVocabularyFactory,
            "redturtle.prenotazioni.requirable_booking_fields",
        )
        required_fields_vocabulary = required_fields_factory(self.context)
        possibly_required_fields = [
            x.token for x in required_fields_vocabulary._terms
        ]
        possibly_visible_fields = [
            "email",
            "phone",
            "subject",
            "agency",
            "fiscalcode",
        ]

        for f in self.widgets.values():
            # If you have a field required by schema, when you fill the field
            # and then empty it you have a red alert without submit the form.
            # In this way all the possibly requred field have the same
            # behaviour: you see the red alert frame only after a submit
            if f.__name__ == "tipology":
                f.required = True
            if f.__name__ == "fullname":
                f.required = True

            if f.__name__ in possibly_required_fields:
                # Zen of python: "Explicit is better than implicit."
                # we could set False this field in schema, but parts of code
                # lines below would be necessary anyway. so I prefer explicit
                # what we are doning
                if f.__name__ in self.context.required_booking_fields:
                    f.required = True
                else:
                    f.required = False
            if (
                f.__name__ in possibly_visible_fields
                and f.__name__ not in self.context.visible_booking_fields
            ):
                f.mode = "hidden"

    @property
    @memoize
    def localized_time(self):
        """ Facade for context/@@plone/toLocalizedTime
        """
        return api.content.get_view(
            "plone", self.context, self.request
        ).toLocalizedTime

    @property
    @memoize
    def label(self):
        """
        Check if user is anonymous
        """
        booking_date = self.booking_DateTime
        if not booking_date:
            return ""
        localized_date = self.localized_time(booking_date)
        return _(
            "label_selected_date",
            u"Selected date: ${date} — Time slot: ${slot}",
            mapping={"date": localized_date, "slot": booking_date.hour()},
        )

    @property
    @memoize
    def description(self):
        """
        Check if user is anonymous
        """
        return _("help_prenotazione_add", u"")

    @property
    @memoize
    def booking_DateTime(self):
        """ Return the booking_date as passed in the request as a DateTime
        object
        """
        booking_date = self.request.form.get("form.booking_date", None)
        if not booking_date:
            booking_date = self.request.form.get(
                "form.widgets.booking_date", None
            )

        if not booking_date:
            return None
        tzname = self.get_timezone()

        if len(booking_date) == 16:
            if tzname == "RMT":
                tzname = "CEST"
            booking_date = " ".join((booking_date, tzname))
        return DateTime(booking_date)

    def get_timezone(self):
        """
        get from environment vars or site settings
        """
        tz = environ.get("TZ", "")
        if tz:
            return tz
        registry = getUtility(IRegistry)
        return registry.get("plone.portal_timezone", None)

    @property
    @memoize
    def is_anonymous(self):
        """
        Check if user is anonymous
        """
        return api.content.get_view(
            "plone_portal_state", self.context, self.request
        ).anonymous()

    @property
    @memoize
    def prenotazioni(self):
        """ Returns the prenotazioni_context_state view.

        Everyone should know about this!
        """
        return api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )

    def do_book(self, data):
        """
        Create a Booking!
        """
        booker = IBooker(self.context.aq_inner)
        referer = self.request.get("HTTP_REFERER", None)
        if referer:
            parsed_url = urlparse(referer)
            params = parse_qs(parsed_url.query)
            if "gate" in params:
                return booker.create(data, force_gate=params["gate"][0])
        return booker.create(data)

    @property
    @memoize
    def back_to_booking_url(self):
        """ This goes back to booking view.
        """
        b_date = self.booking_DateTime
        params = {}
        if b_date:
            params["data"] = b_date.strftime("%d/%m/%Y")
        target = urlify(self.context.absolute_url(), params=params)
        return target

    def exceedes_date_limit(self, data):
        """
        Check if we can book this slot or is it too much in the future.
        """
        future_days = self.context.getFutureDays()
        if not future_days:
            return False
        booking_date = data.get("booking_date", None)
        if not isinstance(booking_date, datetime):
            return False
        date_limit = tznow() + timedelta(future_days)
        if not booking_date.tzinfo:
            tzinfo = date_limit.tzinfo
            if tzinfo:
                booking_date = tzinfo.localize(booking_date)
        if booking_date <= date_limit:
            return False
        return True

    @button.buttonAndHandler(_(u"action_book", u"Book"))
    def action_book(self, action):
        """
        Book this resource
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        required = self.context.required_booking_fields

        # la tipologia di una prenotazione deve essere obbligatoria ticket: 19131
        required.append("tipology")

        for field_id in self.fields.keys():
            if field_id in required and not data.get(field_id, ""):
                raise WidgetActionExecutionError(
                    field_id, Invalid(_(u"Required input is missing."))
                )
        if not data.get("booking_date"):
            raise WidgetActionExecutionError(
                "booking_date", Invalid(_(u"Please provide a booking date"))
            )

        conflict_manager = self.prenotazioni.conflict_manager
        if conflict_manager.conflicts(data):
            msg = _(u"Sorry, this slot is not available anymore.")
            raise WidgetActionExecutionError("booking_date", Invalid(msg))
        if self.exceedes_date_limit(data):
            msg = _(u"Sorry, you can not book this slot for now.")
            raise WidgetActionExecutionError("booking_date", Invalid(msg))

        captcha = getMultiAdapter(
            (aq_inner(self.context), self.request), name="recaptcha"
        )

        if "captcha" in data and not captcha.verify():
            msg = _(u"Please check the captcha")
            raise ActionExecutionError(Invalid(msg))

        obj = self.do_book(data)
        if not obj:
            msg = _(u"Sorry, this slot is not available anymore.")
            api.portal.show_message(
                message=msg, type="warning", request=self.request
            )
            target = self.back_to_booking_url
            return self.request.response.redirect(target)
        msg = _("booking_created")
        api.portal.show_message(message=msg, type="info", request=self.request)
        booking_date = data["booking_date"].strftime("%d/%m/%Y")

        delete_token = IAnnotations(obj).get(DELETE_TOKEN_KEY, "")
        params = {
            "data": booking_date,
            "uid": obj.UID(),
            "delete_token": delete_token,
        }
        target = urlify(
            self.context.absolute_url(),
            paths=["@@prenotazione_print"],
            params=params,
        )
        self.send_email_to_managers(booking=obj)
        return self.request.response.redirect(target)

    @button.buttonAndHandler(
        _(u"action_cancel", default=u"Cancel"), name="cancel"
    )
    def action_cancel(self, action):
        """
        Cancel
        """
        target = self.back_to_booking_url
        return self.request.response.redirect(target)

    def show_message(self, msg, msg_type):
        """ Facade for the show message api function
        """
        show_message = api.portal.show_message
        return show_message(msg, request=self.request, type=msg_type)

    def redirect(self, target, msg="", msg_type="error"):
        """ Redirects the user to the target, optionally with a portal message
        """
        if msg:
            self.show_message(msg, msg_type)
        return self.request.response.redirect(target)

    def has_enough_time(self):
        """ Check if we have enough time to book something
        """
        booking_date = self.booking_DateTime.asdatetime()
        return self.prenotazioni.is_booking_date_bookable(booking_date)

    def __call__(self):
        """ Redirects to the context if no data is found in the request
        """
        # we should always have a booking date
        if not self.booking_DateTime:
            msg = _("please_pick_a_date", "Please select a time slot")
            return self.redirect(self.back_to_booking_url, msg)
        # and if we have it, we should have enough time to do something
        if not self.has_enough_time():
            msg = _(
                "time_slot_to_short",
                "You cannot book any typology at this time",
            )
            return self.redirect(self.back_to_booking_url, msg)
        return super(AddForm, self).__call__()

    def get_mail_from_address(self):
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(
            IMailSchema, prefix="plone", check=False
        )
        from_address = mail_settings.email_from_address
        from_name = mail_settings.email_from_name

        if not from_address:
            return ""
        from_address = from_address.strip()
        mfrom = formataddr((from_name, from_address))
        if parseaddr(mfrom)[1] != from_address:
            mfrom = from_address
        return mfrom

    def send_email_to_managers(self, booking):
        booking_folder = None
        for item in booking.aq_chain:
            if getattr(item, "portal_type", "") == "PrenotazioniFolder":
                booking_folder = item
                break

        email_list = getattr(booking_folder, "email_responsabile", "")
        if email_list:
            mail_template = api.content.get_view(
                name="manager_notification_mail",
                context=booking,
                request=booking.REQUEST,
            )
            parameters = {
                "azienda": getattr(booking, "azienda", ""),
                "booking_folder": booking_folder.title,
                "booking_url": booking.absolute_url(),
                "data_prenotazione": getattr(booking, "data_prenotazione", ""),
                "data_scadenza": getattr(booking, "data_scadenza", ""),
                "description": getattr(booking, "description", ""),
                "email": getattr(booking, "email", ""),
                "fiscalcode": getattr(booking, "fiscalcode", ""),
                "gate": getattr(booking, "gate", ""),
                "phone": getattr(booking, "phone", ""),
                "staff_notes": getattr(booking, "staff_notes", ""),
                "tipologia_prenotazione": getattr(
                    booking, "tipologia_prenotazione", ""
                ),
                "title": getattr(booking, "title", ""),
            }
            mail_text = mail_template(**parameters)

            mailHost = api.portal.get_tool(name="MailHost")
            subject = translate(
                _(
                    "new_booking_admin_notify_subject",
                    default="New booking for ${context}",
                    mapping={"context": booking_folder.title},
                ),
                context=booking.REQUEST,
            )

            for mail in email_list:
                if mail:
                    mailHost.send(
                        mail_text,
                        mto=mail,
                        mfrom=self.get_mail_from_address(),
                        subject=subject,
                        charset="utf-8",
                        msg_type="text/html",
                        immediate=True,
                    )


WrappedAddForm = wrap_form(AddForm)

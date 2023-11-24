# -*- coding: utf-8 -*-
from plone import api
from plone.memoize.view import memoize
from plone.z3cform.layout import wrap_form
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import ActionExecutionError
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getUtility
from zope.interface import Invalid
from zope.interface import implementer
from zope.schema import Text
from zope.schema import TextLine
from zope.schema.interfaces import IVocabularyFactory

from redturtle.prenotazioni import _
from redturtle.prenotazioni import datetime_with_tz
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.browser.week import TIPOLOGIA_PRENOTAZIONE_NAME_COOKIE
from redturtle.prenotazioni.browser.z3c_custom_widget import CustomRadioFieldWidget
from redturtle.prenotazioni.config import REQUIRABLE_AND_VISIBLE_FIELDS
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.utilities.urls import urlify

DEFAULT_REQUIRED_FIELDS = []


class IAddForm(IPrenotazione):

    """
    Interface for creating a prenotazione
    """

    title = TextLine(
        title=_("label_booking_title", "Fullname"), default="", required=True
    )
    description = Text(
        title=_("label_booking_description", "Subject"), default="", required=False
    )


@implementer(IAddForm)
class AddForm(form.AddForm):
    """ """

    render_form = False
    ignoreContext = True

    @property
    def fields_schema(self):
        return field.Fields(IAddForm)

    @property
    def fields(self):
        fields = self.fields_schema
        fields["booking_type"].widgetFactory = CustomRadioFieldWidget

        # omit some fields
        fields = fields.omit("gate").omit("booking_expiration_date")
        fields = fields.omit("staff_notes").omit("booking_code")

        # move title on top (after the type)
        ids = [x for x in fields.keys()]
        ids.insert(2, ids.pop(ids.index("title")))
        fields = fields.select(*ids)

        return fields

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
        possibly_required_fields = [x.token for x in required_fields_vocabulary._terms]

        for f in self.widgets.values():
            # If you have a field required by schema, when you fill the field
            # and then empty it you have a red alert without submit the form.
            # In this way all the possibly requred field have the same
            # behaviour: you see the red alert frame only after a submit
            name = f.__name__
            if name in DEFAULT_REQUIRED_FIELDS:
                f.required = True

            if name in possibly_required_fields:
                # Zen of python: "Explicit is better than implicit."
                # we could set False this field in schema, but parts of code
                # lines below would be necessary anyway. so I prefer explicit
                # what we are doning
                if name in self.context.required_booking_fields:
                    f.required = True
                else:
                    f.required = False
            if (
                name in REQUIRABLE_AND_VISIBLE_FIELDS
                and name not in self.context.visible_booking_fields
            ):
                f.mode = "hidden"

        if not api.user.is_anonymous() and not api.user.has_permission(
            "Modify portal content", obj=self.context
        ):
            user = api.user.get_current()
            for field_name in self.widgets:
                if field_name == "title":
                    value = user.getProperty("fullname", "")
                else:
                    value = user.getProperty(field_name, "")
                if value:
                    self.widgets[field_name].value = value
                    self.widgets[field_name].readonly = "readonly"

    @property
    @memoize
    def localized_time(self):
        """Facade for context/@@plone/toLocalizedTime"""
        return api.content.get_view("plone", self.context, self.request).toLocalizedTime

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
            "Selected date: ${date} — Time: ${slot}",
            mapping={
                "date": localized_date,
                "slot": booking_date.strftime("%H:%M"),
            },
        )

    @property
    @memoize
    def description(self):
        """
        Check if user is anonymous
        """
        return _("help_prenotazione_add", "")

    @property
    @memoize
    def booking_DateTime(self):
        """Return the booking_date as passed in the request as a DateTime
        object
        """
        booking_date = self.request.form.get("form.booking_date", None)
        if not booking_date:
            booking_date = self.request.form.get("form.widgets.booking_date", None)

        if not booking_date:
            return None
        return datetime_with_tz(booking_date)

    @property
    @memoize
    def is_anonymous(self):
        return api.user.is_anonymous()

    @property
    @memoize
    def prenotazioni(self):
        """Returns the prenotazioni_context_state view.

        Everyone should know about this!
        """
        return api.content.get_view(
            "prenotazioni_context_state", self.context, self.request
        )

    @property
    @memoize
    def back_to_booking_url(self):
        """This goes back to booking view."""
        b_date = self.booking_DateTime
        params = {}
        if b_date:
            params["data"] = b_date.strftime("%d/%m/%Y")
        target = urlify(self.context.absolute_url(), params=params)
        return target

    @button.buttonAndHandler(_("action_book", "Book"))
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
        if "booking_type" not in required:
            required.append("booking_type")

        for field_id in self.fields.keys():
            if field_id in required and not data.get(field_id, ""):
                raise WidgetActionExecutionError(
                    field_id, Invalid(_("Required input is missing."))
                )
        if not data.get("booking_date"):
            raise WidgetActionExecutionError(
                "booking_date", Invalid(_("Please provide a booking date"))
            )

        booker = IBooker(self.context.aq_inner)
        try:
            obj = booker.book(data=data)
        except BookerException as e:
            api.portal.show_message(e.args[0], self.request, type="error")
            raise ActionExecutionError(Invalid(e.args[0]))

        msg = _("booking_created")
        api.portal.show_message(message=msg, type="info", request=self.request)
        booking_date = getattr(obj, "booking_date", None).strftime("%d/%m/%Y")

        params = {
            "data": booking_date,
            "uid": obj.UID(),
        }
        target = urlify(
            self.context.absolute_url(),
            paths=["@@prenotazione_print"],
            params=params,
        )

        self.request.response.expireCookie(
            TIPOLOGIA_PRENOTAZIONE_NAME_COOKIE,
            path="/",
        )

        return self.request.response.redirect(target)

    @button.buttonAndHandler(_("action_cancel", default="Cancel"), name="cancel")
    def action_cancel(self, action):
        """
        Cancel
        """
        target = self.back_to_booking_url
        return self.request.response.redirect(target)

    def show_message(self, msg, msg_type):
        """Facade for the show message api function"""
        show_message = api.portal.show_message
        return show_message(msg, request=self.request, type=msg_type)

    def redirect(self, target, msg="", msg_type="error"):
        """Redirects the user to the target, optionally with a portal message"""
        if msg:
            self.show_message(msg, msg_type)
        return self.request.response.redirect(target)

    def has_enough_time(self):
        """Check if we have enough time to book something"""
        booking_date = self.booking_DateTime
        return self.prenotazioni.is_booking_date_bookable(booking_date)

    def __call__(self):
        """Redirects to the context if no data is found in the request"""
        # we should always have a booking date
        if not self.booking_DateTime:
            msg = _("please_pick_a_date", "Please select a time slot")
            return self.redirect(self.back_to_booking_url, msg)
        # and if we have it, we should have enough time to do something
        if not self.has_enough_time():
            msg = _(
                "time_slot_to_short",
                "You cannot book any booking_type at this time",
            )
            return self.redirect(self.back_to_booking_url, msg)
        return super(AddForm, self).__call__()


WrappedAddForm = wrap_form(AddForm)

# -*- coding: utf-8 -*-
from typing import Generator

from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.supermodel import model
from z3c.form import validator
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import provideAdapter
from zope.i18n import translate
from zope.interface import Invalid
from zope.interface import implementer
from zope.interface import invariant
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from redturtle.prenotazioni import _
from redturtle.prenotazioni.browser.widget import WeekTableOverridesFieldWidget
from redturtle.prenotazioni.config import DEFAULT_VISIBLE_BOOKING_FIELDS
from redturtle.prenotazioni.content.prenotazione_type import PrenotazioneType
from redturtle.prenotazioni.content.validators import PauseValidator
from redturtle.prenotazioni.content.validators import checkOverrides

try:
    from plone.app.dexterity import textindexer
except ImportError:
    # Plone 5.2
    from collective import dexteritytextindexer as textindexer


def get_dgf_values_from_request(request, fieldname, columns=[]):
    """
    Validator with datagridfield works in a fuzzy way. We need to extract
    values from request to be sure we are validating correct data.
    """

    def get_from_form(form, fieldname):
        value = form.get(fieldname, None)
        if value:
            if isinstance(value, list):
                return value[0]
            if isinstance(value, str):
                return value
        return None

    number_of_entry = request.form.get("form.widgets.{}.count".format(fieldname))
    data = []
    prefix = "form.widgets.{}".format(fieldname)
    for counter in range(int(number_of_entry)):
        row_data = {}
        for column in columns:
            indexed_prefix = "{}.{}.widgets.".format(prefix, counter)
            row_data.update(
                {
                    column: get_from_form(
                        request.form, "{}{}".format(indexed_prefix, column)
                    )
                }
            )
        data.append(row_data)
    return data


class IWeekTableRow(model.Schema):
    day = schema.TextLine(
        title=_("day_label", default="Day of week"),
        required=True,
        default="",
    )
    # TODO: sarebbe bello, ma datagrid non funziona:
    # su plone si rompe, su volto non considera il mode=display
    # ancora peggio readonly=true sul field
    # form.mode(day="display")
    morning_start = schema.Choice(
        title=_("morning_start_label", default="Start time in the morning"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )
    morning_end = schema.Choice(
        title=_("morning_end_label", default="End time in the morning"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )

    afternoon_start = schema.Choice(
        title=_("afternoon_start_label", default="Start time in the afternoon"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )

    afternoon_end = schema.Choice(
        title=_("afternoon_end_label", default="End time in the afternoon"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )


class IPauseTableRow(model.Schema):
    day = schema.Choice(
        title=_("day_label", default="Day of week"),
        required=True,
        vocabulary=SimpleVocabulary(
            [
                SimpleTerm(value=None, token=None, title=_("Select a day")),
                SimpleTerm(value="0", token="0", title=_("Monday")),
                SimpleTerm(value="1", token="1", title=_("Tuesday")),
                SimpleTerm(value="2", token="2", title=_("Wednesday")),
                SimpleTerm(value="3", token="3", title=_("Thursday")),
                SimpleTerm(value="4", token="4", title=_("Friday")),
                SimpleTerm(value="5", token="5", title=_("Saturday")),
                SimpleTerm(value="6", token="6", title=_("Sunday")),
            ]
        ),
    )
    pause_start = schema.Choice(
        title=_("pause_start_label", default="Pause start"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )
    pause_end = schema.Choice(
        title=_("pause_end_label", default="Pause end"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _("notify_on_submit_subject_default_value", "Booking created ${title}")
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_submit_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} was created.<a href=${booking_print_url}>Link</a>",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_subject_default_value",
            "Booking of ${booking_date} at ${booking_time} was accepted",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_message_default_value",
            "The booking${booking_type} for ${title} was confirmed! <a href=${booking_print_url}>Link</a>",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_subject_default_value",
            "Modified the boolking date for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_message_default_value",
            "The booking scheduling of ${booking_type} was modified."
            "The new one is on ${booking_date} at ${booking_time}. <a href=${booking_print_url}>Link</a>.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_subject_default_value",
            "Booking refused for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


class IPrenotazioniFolder(model.Schema):
    """Marker interface and Dexterity Python Schema for PrenotazioniFolder"""

    textindexer.searchable("descriptionAgenda")
    descriptionAgenda = RichText(
        required=False,
        title=_("Descrizione Agenda", default="Descrizione Agenda"),
        description=_("Inserire il testo di presentazione dell'agenda corrente"),
    )

    form.mode(descriptionAgenda="display")

    directives.widget(visible_booking_fields=CheckBoxFieldWidget)
    visible_booking_fields = schema.List(
        title=_("label_visible_booking_fields", default="Visible booking fields"),
        description=_(
            "help_visible_booking_fields",
            "User will not be able to add a booking unless those "
            "fields are filled. "
            "Remember that, whatever you selected in this list, "
            "users have to supply at least one "
            'of "Email" or "Telephone"',
        ),
        required=False,
        default=DEFAULT_VISIBLE_BOOKING_FIELDS,
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.requirable_booking_fields"
        ),
    )

    directives.widget(required_booking_fields=CheckBoxFieldWidget)
    required_booking_fields = schema.List(
        title=_("label_required_booking_fields", default="Required booking fields"),
        description=_(
            "help_required_booking_fields",
            "User will not be able to add a booking unless those "
            "fields are filled. "
            "Remember that, whatever you selected in this list, "
            "users have to supply at least one "
            'of "Email", "Mobile", or "Telephone"',
        ),
        required=False,
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.requirable_booking_fields"
        ),
    )

    daData = schema.Date(title=_("Data inizio validità"))

    aData = schema.Date(
        title=_("Data fine validità"),
        description=_(
            "aData_help",
            default="Leave empty, and this Booking Folder will never expire",
        ),  # noqa
        required=False,
    )

    def get_options():
        """Return the options for this widget"""
        options = [
            SimpleTerm(value="yes", token="yes", title=_("Yes")),
            SimpleTerm(value="no", token="no", title=_("No")),
        ]

        return SimpleVocabulary(options)

    same_day_booking_disallowed = schema.Choice(
        title=_(
            "label_same_day_booking_disallowed",
            default="Disallow same day booking",
        ),
        description=_(
            "help_same_day_booking_disallowed",
            "States if it is not allowed to reserve a booking "
            "during the current day",
        ),
        required=True,
        source=get_options(),
    )

    week_table = schema.List(
        title=_("Week table"),
        description=_("Insert week table schema."),
        required=True,
        value_type=DictRow(title="week row", schema=IWeekTableRow),
        default=[
            {
                "day": "Lunedì",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Martedì",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Mercoledì",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Giovedì",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Venerdì",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Sabato",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
            {
                "day": "Domenica",
                "morning_start": None,
                "afternoon_start": None,
                "morning_end": None,
                "afternoon_end": None,
            },
        ],
    )
    form.widget(
        "week_table",
        DataGridFieldFactory,
        allow_insert=False,
        allow_delete=False,
        allow_reorder=False,
        auto_append=False,
        frontendOptions={"widget": "data_grid"},
    )

    week_table_overrides = schema.SourceText(
        title=_("week_table_overrides_label", default="Week table overrides"),
        description=_(
            "week_table_overrides_help",
            default="Insert here week schema for some custom date intervals.",
        ),
        required=False,
        constraint=checkOverrides,
    )
    form.widget("week_table_overrides", WeekTableOverridesFieldWidget)
    pause_table = schema.List(
        title=_("Pause table"),
        description=_("Insert pause table schema."),
        required=False,
        value_type=DictRow(title="Pause row", schema=IPauseTableRow),
    )
    form.widget(
        "pause_table",
        DataGridFieldFactory,
        auto_append=False,
        frontendOptions={"widget": "data_grid"},
    )

    holidays = schema.List(
        title=_("holidays_label", default="Holidays"),
        description=_(
            "holidays_help",
            default="Set holidays (one for line) "
            "in DD/MM/YYYY. you can write * for the year, if this event is "
            "yearly.",
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[
            "01/01/*",
            "06/01/*",
            "25/04/*",
            "01/05/*",
            "02/06/*",
            "15/08/*",
            "01/11/*",
            "08/12/*",
            "25/12/*",
            "26/12/*",
        ],
    )

    futureDays = schema.Int(
        default=0,
        title=_("Max days in the future"),
        description=_(
            "futureDays",
            default="Limit booking in the future to an amount "
            "of days in the future starting from "
            "the current day. \n"
            "Keep 0 to give no limits.",
        ),
    )

    notBeforeDays = schema.Int(
        default=2,
        title=_("Days booking is not allowed before"),
        description=_(
            "notBeforeDays",
            default="Booking is not allowed before the amount "
            "of days specified. \n"
            "Keep 0 to give no limits.",
        ),
    )

    gates = schema.List(
        title=_("gates_label", "Gates"),
        description=_("gates_help", default="Put gates here (one per line)."),
        required=True,
        value_type=schema.TextLine(),
        default=[],
    )

    auto_confirm = schema.Bool(
        title=_("auto_confirm", default="Automatically confirm."),
        description=_(
            "auto_confirm_help",
            default="All bookings will be automatically accepted.",
        ),
        default=False,
        required=False,
    )
    # XXX validate email
    email_responsabile = schema.List(
        title=_("Responsible email"),
        description=_(
            "Insert a list of email addresses that will be notified when new "
            "bookings get created."
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[],
    )

    @invariant
    def data_validation(data):
        """
        Needed because is the only way to validate a datagrid field
        """
        for interval in data.week_table:
            if interval["morning_start"] and not interval["morning_end"]:
                raise Invalid(_("You should set an end time for morning."))
            if interval["morning_end"] and not interval["morning_start"]:
                raise Invalid(_("You should set a start time for morning."))
            if interval["afternoon_start"] and not interval["afternoon_end"]:
                raise Invalid(_("You should set an end time for afternoon."))
            if interval["afternoon_end"] and not interval["afternoon_start"]:
                raise Invalid(_("You should set a start time for afternoon."))
            if interval["morning_start"] and interval["morning_end"]:
                if interval["morning_start"] > interval["morning_end"]:
                    raise Invalid(_("Morning start should not be greater than end."))
            if interval["afternoon_start"] and interval["afternoon_end"]:
                if interval["afternoon_start"] > interval["afternoon_end"]:
                    raise Invalid(_("Afternoon start should not be greater than end."))

    # TODO: definire o descrivere quando avviee la notifica
    # TODO: inserire qui la chiave IO ? o su un config in zope.conf/environment ?
    app_io_enabled = schema.Bool(
        title=_("App IO notification"),
        default=False,
        required=False,
    )

    notify_on_submit = schema.Bool(
        title=_("notify_on_submit", default="Notify when created."),
        description=_(
            "notify_on_submit_help",
            default="Notify via mail the user when his booking has been created. If auto-confirm flag is selected and confirm notify is selected, this one will be ignored.",
        ),
        default=False,
        required=False,
    )
    notify_on_confirm = schema.Bool(
        title=_("notify_on_confirm", default="Notify when confirmed."),
        description=_(
            "notify_on_confirm_help",
            default="Notify via mail the user when his booking has been confirmed.",
        ),
        default=False,
        required=False,
    )
    notify_on_move = schema.Bool(
        title=_("notify_on_move", default="Notify when moved."),
        description=_(
            "notify_on_move_help",
            default="Notify via mail the user when his booking has been moved.",
        ),
        default=False,
        required=False,
    )
    notify_on_refuse = schema.Bool(
        title=_("notify_on_refuse", default="Notify when rejected."),
        description=_(
            "notify_on_refuse_help",
            default="Notify via mail the user when his booking has been rejected.",
        ),
        default=False,
        required=False,
    )
    notify_on_submit_subject = schema.TextLine(
        title=_(
            "notify_on_submit_subject",
            default="Prenotazione created notification subject.",
        ),
        description=_("notify_on_submit_subject_help", default=""),
        defaultFactory=notify_on_submit_subject_default_factory,
        required=False,
    )
    notify_on_submit_message = schema.Text(
        title=_(
            "notify_on_submit_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_submit_message_help", default=""),
        defaultFactory=notify_on_submit_message_default_factory,
        required=False,
    )
    notify_on_confirm_subject = schema.TextLine(
        title=_(
            "notify_on_confirm_subject",
            default="Prenotazione confirmed notification subject.",
        ),
        description=_("notify_on_confirm_subject_help", default=""),
        defaultFactory=notify_on_confirm_subject_default_factory,
        required=False,
    )
    notify_on_confirm_message = schema.Text(
        title=_(
            "notify_on_confirm_message",
            default="Prenotazione confirmed notification message.",
        ),
        description=_("notify_on_confirm_message_help", default=""),
        defaultFactory=notify_on_confirm_message_default_factory,
        required=False,
    )
    notify_on_move_subject = schema.TextLine(
        title=_(
            "notify_on_move_subject",
            default="Prenotazione moved notification subject.",
        ),
        description=_("notify_on_move_subject_help", default=""),
        defaultFactory=notify_on_move_subject_default_factory,
        required=False,
    )
    notify_on_move_message = schema.Text(
        title=_(
            "notify_on_move_message",
            default="Prenotazione moved notification message.",
        ),
        description=_("notify_on_move_message_help", default=""),
        defaultFactory=notify_on_move_message_default_factory,
        required=False,
    )
    notify_on_refuse_subject = schema.TextLine(
        title=_(
            "notify_on_refuse_subject",
            default="Prenotazione refused notification subject.",
        ),
        description=_("notify_on_refuse_subject_help", default=""),
        defaultFactory=notify_on_refuse_subject_default_factory,
        required=False,
    )
    notify_on_refuse_message = schema.Text(
        title=_(
            "notify_on_refuse_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_refuse_message_help", default=""),
        defaultFactory=notify_on_refuse_message_default_factory,
        required=False,
    )

    max_bookings_allowed = schema.Int(
        title=_(
            "max_bookings_allowed_label",
            default="Maximum bookings number allowed",
        ),
        description=_(
            "max_bookings_allowed_description",
            default="The number of simultaneous bookings allowed for the same user.",
        ),
        required=False,
        default=0,
    )

    model.fieldset(
        "dates",
        label=_("Date validità"),
        fields=[
            "daData",
            "aData",
            "same_day_booking_disallowed",
            "holidays",
            "futureDays",
            "notBeforeDays",
        ],
    )

    model.fieldset(
        "week_table",
        label=_("Week table"),
        fields=[
            "week_table",
            "pause_table",
        ],
    )

    model.fieldset(
        "week_table_overrides",
        label=_("week_table_overrides_label", default="Week table overrides"),
        fields=[
            "week_table_overrides",
        ],
    )

    model.fieldset(
        "Notifications",
        label=_("notifications_label", default="Notifications"),
        fields=[
            "notify_on_submit",
            "notify_on_confirm",
            "notify_on_move",
            "notify_on_refuse",
        ],
    )
    model.fieldset(
        "Prenotazioni Email Templates",
        label=_(
            "prenotazioni_email_templates_label",
            default="Testo delle email di notifica",
        ),
        # TODO: Use custom frontend widget for the new
        # field where we must render the html of field's description
        # description=_(
        #     "templates_usage_default_value",
        #     "${title} - title."
        #     "${booking_gate} - booking gate."
        #     "${booking_human_readable_start} - booking human readable start."
        #     "${booking_date} - booking date."
        #     "${booking_end_date} - booking end date."
        #     "${booking_time} - booking time."
        #     "${booking_time_end} - booking time end."
        #     "${booking_code} - booking code."
        #     "${booking_type} - booking type."
        #     "${booking_print_url} - booking print url."
        #     "${booking_url_with_delete_token} - booking url with delete token."
        #     "${booking_user_phone} - booking user phone."
        #     "${booking_user_email} - booking user email."
        #     "${booking_user_details} - booking user details."
        #     "${booking_office_contact_phone} - booking office contact phone."
        #     "${booking_office_contact_pec} - booking office contact pec."
        #     "${booking_office_contact_fax} - booking office contact fax."
        #     "${booking_how_to_get_to_office} - booking how to get to office."
        #     "${booking_office_complete_address} - booking office complete address.",
        #     "${booking_user_details} - booking user details",
        #     "${booking_requirements} - booking requeirements.",
        #     "${prenotazioni_folder_title} - prenotazioni folder title.",
        # ),
        # description=_(
        #     "prenotazioni_email_templates_description",
        #     default="",
        # ),
        fields=[
            "notify_on_submit_subject",
            "notify_on_submit_message",
            "notify_on_confirm_subject",
            "notify_on_confirm_message",
            "notify_on_move_subject",
            "notify_on_move_message",
            "notify_on_refuse_subject",
            "notify_on_refuse_message",
        ],
    )
    model.fieldset(
        "Reminders",
        label=_("reminders_label", default="Reminders"),
        fields=[
            "app_io_enabled",
        ],
    )


validator.WidgetValidatorDiscriminators(
    PauseValidator, field=IPrenotazioniFolder["pause_table"]
)
provideAdapter(PauseValidator)


@implementer(IPrenotazioniFolder)
class PrenotazioniFolder(Container):
    """ """

    def getDescriptionAgenda(self):
        return self.descriptionAgenda

    def getGates(self):
        return self.gates

    def getDaData(self):
        return self.daData

    def getAData(self):
        return self.aData

    def getFutureDays(self):
        return self.futureDays

    def getNotBeforeDays(self):
        return self.notBeforeDays

    def get_booking_types(self) -> Generator[PrenotazioneType, None, None]:
        return self.listFolderContents(
            contentFilter={"portal_type": "PrenotazioneType"}
        )

    # BBB: compatibility with old code (booking_types was a List of IBookingTypeRow)
    @property
    def booking_types(self):
        return [
            {
                "name": t.title,
                "duration": t.duration,
                "hidden": getattr(t, "hidden", False),
            }
            for t in self.get_booking_types()
        ]

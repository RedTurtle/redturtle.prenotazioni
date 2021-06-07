# -*- coding: utf-8 -*-
from collective import dexteritytextindexer
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from datetime import date
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.supermodel import model
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.slot import (
    interval_is_contained,
    is_intervals_overlapping,
)
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import Invalid
from zope.interface import invariant
from zope.component import provideAdapter
from z3c.form import validator


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

    number_of_entry = request.form.get(
        "form.widgets.{}.count".format(fieldname)
    )
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
        title=_("day_label", default="Day of week"), required=True, default=""
    )
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
        title=_(
            "afternoon_start_label", default="Start time in the afternoon"
        ),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )

    afternoon_end = schema.Choice(
        title=_("afternoon_end_label", default="End time in the afternoon"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )


class IPauseTableRow(model.Schema):
    def get_options():  # noqa
        """ Return the options for the day widget
        """
        options = [
            SimpleTerm(value=None, token=None, title=_("Select a day")),
            SimpleTerm(value=0, token=0, title=_("Monday")),
            SimpleTerm(value=1, token=1, title=_("Tuesday")),
            SimpleTerm(value=2, token=2, title=_("Wednesday")),
            SimpleTerm(value=3, token=3, title=_("Thursday")),
            SimpleTerm(value=4, token=4, title=_("Friday")),
            SimpleTerm(value=5, token=5, title=_("Saturday")),
            SimpleTerm(value=6, token=6, title=_("Sunday")),
        ]
        return SimpleVocabulary(options)

    day = schema.Choice(
        title=_("day_label", default="Day of week"),
        required=True,
        source=get_options(),
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


class IBookingTypeRow(Interface):
    name = schema.TextLine(title=_("Typology name"), required=True)
    duration = schema.Choice(
        title=_("Duration value"),
        required=True,
        vocabulary="redturtle.prenotazioni.VocDurataIncontro",
    )


class IPrenotazioniFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for PrenotazioniFolder
    """

    dexteritytextindexer.searchable("descriptionAgenda")
    descriptionAgenda = RichText(
        required=False,
        title=_("Descrizione Agenda", default="Descrizione Agenda"),
        description=(
            "Inserire il testo di presentazione " "dell'agenda corrente"
        ),
    )

    directives.widget(required_booking_fields=CheckBoxFieldWidget)
    required_booking_fields = schema.List(
        title=_(
            "label_required_booking_fields", default="Required booking fields"
        ),
        description=_(
            "help_required_booking_fields",
            "User will not be able to add a booking unless those "
            "fields are filled. "
            "Remember that, "
            "whatever you selected in this list, "
            "users have to supply at least one "
            u'of "Email", "Mobile", or "Telephone"',
        ),
        required=False,
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.requirable_booking_fields"
        ),
    )

    directives.widget(required_booking_fields=CheckBoxFieldWidget)

    visible_booking_fields = schema.List(
        title=_(
            "label_visible_booking_fields", default="Visible booking fields"
        ),
        description=_(
            "help_visible_booking_fields",
            "User will not be able to add a booking unless those "
            "fields are filled. "
            "Remember that, "
            "whatever you selected in this list, "
            "users have to supply at least one "
            u'of "Email" or "Telephone"',
        ),
        required=False,
        default=["email", "phone", "subject"],
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.requirable_booking_fields"
        ),
    )
    directives.widget(visible_booking_fields=CheckBoxFieldWidget)

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
        """ Return the options for this widget
        """
        today = date.today().strftime("%Y/%m/%d")
        options = [
            SimpleTerm(value="yes", token="yes", title=_("Yes")),
            SimpleTerm(value="no", token="no", title=_("No")),
            SimpleTerm(
                value=today, token=today, title=_("No, just for today")
            ),
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
    form.widget(week_table=DataGridFieldFactory)

    pause_table = schema.List(
        title=_("Pause table"),
        description=_("Insert pause table schema."),
        required=False,
        value_type=DictRow(title="Pause row", schema=IPauseTableRow),
    )
    form.widget(pause_table=DataGridFieldFactory)

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
        default=[],
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

    booking_types = schema.List(
        title=_("booking_types_label", default="Booking types"),
        description=_(
            "booking_types_help",
            default="Put booking types there (one per line).\n"
            "If you do not provide this field, "
            "not type selection will be available",
        ),
        value_type=DictRow(schema=IBookingTypeRow),
    )
    form.widget(booking_types=DataGridFieldFactory)

    gates = schema.List(
        title=_("gates_label", "Gates"),
        description=_(
            "gates_help",
            default="Put gates here (one per line)."
        ),
        required=True,
        value_type=schema.TextLine(),
        default=[],
    )

    unavailable_gates = schema.List(
        title=_("unavailable_gates_label", "Unavailable gates"),
        description=_(
            "unavailable_gates_help",
            default="Add a gate here (one per line) if, "
            "for some reason, "
            "it is not be available."
            "The specified gate will not be taken in to "  # noqa
            "account for slot allocation. "
            "Each line should match a corresponding "
            u'line in the "Gates" field',
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[],
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

    how_to_get_here = schema.Text(
        required=False,
        title=_("How to get here", default="How to get here"),
        description=_("Insert here indications on how to reach the office"),
    )

    phone = schema.TextLine(
        title=_("Contact phone"),
        description=_("Insert here the contact phone"),
        required=False,
    )

    fax = schema.TextLine(
        title=_("Contact fax"),
        description=_("Insert here the contact fax"),
        required=False,
    )

    pec = schema.TextLine(
        title=_("Contact PEC"),
        description=_("Insert here the contact PEC"),
        required=False,
    )

    complete_address = schema.Text(
        required=False,
        title=_("Complete address", default="Complete address"),
        description=_("Insert here the complete office address"),
    )

    model.fieldset(
        "contacts",
        label=_("contacts_label", default=u"Contacts"),
        description=_(
            "contacts_help",
            default=u"Show here contacts information that will be used by authomatic mail system",  # noqa
        ),
        fields=["how_to_get_here", "phone", "fax", "pec", "complete_address"],
    )

    @invariant
    def data_validation(data):
        if not data.booking_types:
            raise Invalid(_(u"You should set at least one booking type."))
        for interval in data.week_table:
            if interval["morning_start"] and not interval["morning_end"]:
                raise Invalid(_(u"You should set and end time for morning."))
            if interval["morning_end"] and not interval["morning_start"]:
                raise Invalid(_(u"You should set a start time for morning."))
            if interval["afternoon_start"] and not interval["afternoon_end"]:
                raise Invalid(_(u"You should set and end time for afternoon."))
            if interval["afternoon_end"] and not interval["afternoon_start"]:
                raise Invalid(_(u"You should set a start time for afternoon."))
            if interval["morning_start"] and interval["morning_end"]:
                if interval["morning_start"] > interval["morning_end"]:
                    raise Invalid(
                        _(u"Morning start should not be greater than end.")
                    )
            if interval["afternoon_start"] and interval["afternoon_end"]:
                if interval["afternoon_start"] > interval["afternoon_end"]:
                    raise Invalid(
                        _(u"Afternoon start should not be greater than end.")
                    )


class PauseValidator(validator.SimpleFieldValidator):
    """z3c.form validator class for international phone numbers
    """

    def validate(self, pause_table):
        """Validate international phone number on input
        """
        super(PauseValidator, self).validate(pause_table)
        pause_table = get_dgf_values_from_request(
            self.context.REQUEST,
            "pause_table",
            ["day", "pause_start", "pause_end"],
        )
        if not pause_table:
            return

        week_table = get_dgf_values_from_request(
            self.context.REQUEST,
            "week_table",
            [
                "day",
                "morning_start",
                "morning_end",
                "afternoon_start",
                "afternoon_end",
            ],
        )

        # validate pauses
        groups_of_pause = {}
        for pause in pause_table:
            groups_of_pause.setdefault(pause["day"], []).append(pause)

        for day in groups_of_pause:
            day_hours = week_table[int(day)]
            for pause in groups_of_pause[day]:
                #  0. Of course if we don't have a correct interval we can't do
                # more steps
                if (
                    pause["pause_end"] == "--NOVALUE--"
                    or pause["pause_start"] == "--NOVALUE--"
                ):
                    raise Invalid(_(u"You must set both start and end"))

                # 1. Pause starts should always be bigger than pause ends
                if not (pause["pause_end"] > pause["pause_start"]):
                    raise Invalid(
                        _(u"Pause end should be greater than pause start")
                    )
                interval = [pause["pause_start"], pause["pause_end"]]
                # 2. a pause interval should always be contained in the morning
                # or afternoon defined for these days
                if not (
                    interval_is_contained(
                        interval,
                        day_hours["morning_start"],
                        day_hours["morning_end"],
                    )
                    or interval_is_contained(
                        interval,
                        day_hours["afternoon_start"],
                        day_hours["afternoon_end"],
                    )
                ):
                    raise Invalid(
                        _(
                            u"Pause should be included in morning slot or afternoon slot"  # noqa
                        )
                    )
            # 3. two pause interval on the same day should not overlap
            if is_intervals_overlapping(
                [
                    (pause["pause_start"], pause["pause_end"])
                    for pause in groups_of_pause[day]
                ]
            ):
                raise Invalid(
                    _(u"In the same day there are overlapping intervals")
                )  # noqa


validator.WidgetValidatorDiscriminators(
    PauseValidator, field=IPrenotazioniFolder["pause_table"]
)
provideAdapter(PauseValidator)


@implementer(IPrenotazioniFolder)
class PrenotazioniFolder(Container):
    """
    """

    def getDescriptionAgenda(self):
        return self.descriptionAgenda

    def getGates(self):
        return self.gates

    def getUnavailable_gates(self):
        return self.unavailable_gates

    def getDaData(self):
        return self.daData

    def getAData(self):
        return self.aData

    def getFutureDays(self):
        return self.futureDays

    def getNotBeforeDays(self):
        return self.notBeforeDays

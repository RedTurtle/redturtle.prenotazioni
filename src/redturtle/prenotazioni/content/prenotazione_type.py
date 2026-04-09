# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.supermodel import model
from redturtle.prenotazioni import _
from zope import schema
from zope.interface import implementer
from zope.interface import invariant


def get_time_range_duration_minutes(start_time, end_time):
    """Return the interval between two time values in minutes.

    start_time e end_time sono stringe nella forma "HHMM"
    """
    if isinstance(start_time, str) and len(start_time) == 4 and start_time.isdigit():
        start = int(start_time[:2]) * 60 + int(start_time[2:])
    else:
        ValueError(f"invalid start_time {start_time}")
    if isinstance(end_time, str) and len(end_time) == 4 and end_time.isdigit():
        end = int(end_time[:2]) * 60 + int(end_time[2:])
    else:
        ValueError(f"invalid start_time {start_time}")
    return end - start


class IBookingAdditionalFieldsSchema(model.Schema):
    # TODO: definire un validatore per fare in modo che il nome sia unico e
    #       che non contenga caratteri strani non ammessi
    name = schema.TextLine(
        title=_("booking_additional_field_name", default="id"),
        required=True,
        default="",
        description=_(
            "booking_additional_field_name_help",
            default="Additional field id must be unique",
        ),
    )
    label = schema.TextLine(
        title=_("booking_additional_field_label", default="Label"),
        required=True,
        default="",
    )
    type = schema.Choice(
        title=_("booking_additional_field_type", default="Tipo"),
        required=True,
        vocabulary="redturtle.prenotazioni.booking_additional_fields_types",
    )
    required = schema.Bool(
        title=_("booking_additional_field_required", default="Required"),
        required=False,
        default=False,
    )
    description = schema.TextLine(
        title=_("booking_additional_field_description", default="Descrizione"),
        required=False,
        default="",
    )


class IPrenotazioneType(model.Schema):
    """Marker interface and Dexterity Python Schema for Prenotazione"""

    duration = schema.Choice(
        title=_("booking_type_duration_label", default="Duration value"),
        required=False,
        vocabulary="redturtle.prenotazioni.VocDurataIncontro",
        description=_(
            "booking_type_duration_help",
            default="The duration of the booking in minutes. If start and end time are specified, this value will be overridden.",
        ),
    )

    # Se start_time ed end_time sono valorizzati, "duration" viene calcolato automaticamente
    # come intervallo temporale espresso in minuti.
    # L'esistenza di questi campi permette di gestire tipologie di prenotazione con tempi fissati
    # all'interno della giornata (es. 9:00-9:30) invece di far scegliere al sistema l'orario di prenotazione
    # guardando solo la durata
    start_time = schema.Choice(
        title=_("booking_type_start_time_label", default="Start Time"),
        required=False,
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        description=_(
            "prenotazione_type_start_time_help",
            default="The fixed start time for this booking type. If specified, the end time must be specified as well.",
        ),
    )
    end_time = schema.Choice(
        title=_("booking_type_end_time_label", default="End Time"),
        required=False,
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        description=_(
            "prenotazione_type_end_time_help",
            default="The fixed end time for this booking type. If specified, the start time must be specified as well.",
        ),
    )

    @invariant
    def validate_time_range(data):

        # 1. Se si specifica solo uno dei campi "start_time" e "end_time" non va bene
        if (data.start_time and not data.end_time) or (
            not data.start_time and data.end_time
        ):
            raise schema.ValidationError(
                _(
                    "booking_type_duration_or_time_error",
                    default="You have to specify both start and end time, or leave both empty.",
                )
            )

        # 2. Se si specificano entrambi allora "duration" deve corrispondere all'intervallo
        #    temporale fra di loro oppure essere vuota
        if data.start_time and data.end_time:
            duration_minutes = get_time_range_duration_minutes(
                data.start_time,
                data.end_time,
            )

            if duration_minutes <= 0:
                raise schema.ValidationError(
                    _(
                        "booking_type_invalid_time_range_error",
                        default="End time must be greater than start time.",
                    )
                )

            if data.duration and int(data.duration) != duration_minutes:
                raise schema.ValidationError(
                    _(
                        "booking_type_duration_or_time_mismatch_error",
                        default="Duration value doesn't match the provided time range.",
                    )
                )

        # 3. Deve essere specificato almeno un valore fra "duration" e "start_time"/"end_time"
        if not data.start_time and not data.end_time and not data.duration:
            raise schema.ValidationError(
                _(
                    "booking_type_duration_or_time_required_error",
                    default="You have to specify a duration value or a time range.",
                )
            )

    requirements = RichText(
        required=False,
        title=_("booking_type_requirements_labled", default="Requirements"),
        description=_(
            "booking_type_requirements_help",
            default="List of requirements to recieve the service",
        ),
    )

    booking_details_help_text = RichText(
        required=False,
        title=_("booking_details_help_text_label", default="Booking detail help text"),
        description=_(
            "booking_details_help_text_label_help",
            default='This field will be visualized as "Details" helptext during the booking steps',
        ),
    )

    booking_additional_fields_schema = schema.List(
        title=_(
            "booking_additional_fields_schema_title",
            default="Booking additional fields schema",
        ),
        default=[],
        value_type=DictRow(schema=IBookingAdditionalFieldsSchema),
        description=_(
            "booking_additional_fields_schema_description",
            default="This schema is being used for the additional booking fields",
        ),
        required=False,
    )

    form.widget(
        "booking_additional_fields_schema",
        DataGridFieldFactory,
        frontendOptions={
            "widget": "data_grid",
        },
    )

    model.fieldset(
        "additional_fields",
        label=_("booking_additional_fields_schema_title"),
        fields=[
            "booking_additional_fields_schema",
        ],
    )


@implementer(IPrenotazioneType)
class PrenotazioneType(Item):
    """ """

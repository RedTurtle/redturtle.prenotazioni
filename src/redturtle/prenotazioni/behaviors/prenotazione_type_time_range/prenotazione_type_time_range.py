# -*- coding: utf-8 -*-
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from redturtle.prenotazioni import _
from redturtle.prenotazioni.content.prenotazione_type import (
    get_time_range_duration_minutes,
)
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import invariant
from zope.interface import provider


@provider(IFormFieldProvider)
class IPrenotazioneTypeTimeRange(model.Schema):
    """Fixed time range fields for PrenotazioneType."""

    # Il campo duration è sovrascitto qui per togliere il requisito di essere obbligatorio,
    # visto che se start_time ed end_time sono valorizzati allora duration viene calcolato
    # automaticamente e non è necessario specificarlo.
    # E per peremettere di avere il validatore invariant.
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


@implementer(IPrenotazioneTypeTimeRange)
@adapter(IDexterityContent)
class PrenotazioneTypeTimeRange:
    """Behavior adapter for fixed time range fields."""

    def __init__(self, context):
        self.context = context


def update_duration_from_time_range(obj, event):
    """Keep duration aligned with start/end time when both are provided."""
    start_time = getattr(obj, "start_time", None)
    end_time = getattr(obj, "end_time", None)

    if not start_time or not end_time:
        return

    duration_minutes = get_time_range_duration_minutes(start_time, end_time)
    computed_duration = str(duration_minutes)
    if getattr(obj, "duration", None) != computed_duration:
        obj.duration = computed_duration

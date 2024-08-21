# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from collective.z3cform.datagridfield.row import DictRow

from redturtle.prenotazioni import _


class IPrenotazioneType(model.Schema):
    """Marker interface and Dexterity Python Schema for Prenotazione"""

    duration = schema.Choice(
        title=_("booking_type_duration_label", default="Duration value"),
        required=True,
        vocabulary="redturtle.prenotazioni.VocDurataIncontro",
    )

    requirements = RichText(
        required=False,
        title=_("booking_type_requirements_labled", default="Requirements"),
        description=_(
            "booking_type_requirements_help",
            default="List of requirements to recieve the service",
        ),
    )

    # gates = schema.List(
    #     title=_("gates_label", default="Gates"),
    #     description=_("gates_help", default="Put gates here (one per line)."),
    #     required=True,
    #     value_type=schema.Choice(
    #         vocabulary="redturtle.prenotazioni.VocPrenotazioneTypeGates"
    #     ),
    #     default=[],
    # )

    booking_details_help_text = RichText(
        required=False,
        title=_("booking_details_help_text_label", default="Bookign detail help text"),
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
        value_type=DictRow(schema=ITempiEScadenzeValueSchema),
        description=_(
            "timeline_tempi_scadenze_help",
            default="Timeline tempi e scadenze del servizio: indicare per ogni "
            "scadenza un titolo descrittivo ed un eventuale sottotitolo. "
            "Per ogni scadenza, selezionare opzionalmente o l'intervallo (Campi"
            ' "Intervallo" e "Tipo Intervallo", es. "1" e "settimana"),'
            ' oppure direttamente una data di scadenza (campo: "Data Scadenza"'
            ", esempio 31/12/2023). "
            'Se vengono compilati entrambi, ha priorità il campo "Data Scadenza".',
        ),
        required=False,
    )


@implementer(IPrenotazioneType)
class PrenotazioneType(Item):
    """ """

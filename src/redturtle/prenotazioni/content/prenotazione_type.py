# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from redturtle.prenotazioni import _


class IBookingAdditionalFieldsSchema(model.Schema):
    name = schema.TextLine(
        title=_("booking_additional_fieldname", default="Name"),
        required=True,
        default="",
    )
    description = schema.TextLine(
        title=_("booking_additional_field_description", default="Descrizione"),
        required=False,
        default="",
    )
    type = schema.Choice(
        title=_("booking_additional_field_type", default="Tipo"),
        required=True,
        vocabulary="redturtle.prenotazioni.booking_additional_fields_types",
    )


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
        value_type=DictRow(schema=IBookingAdditionalFieldsSchema),
        description=_(
            "booking_additional_fields_schema_description",
            default="This schema is being used for the additional bookign fields",
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


@implementer(IPrenotazioneType)
class PrenotazioneType(Item):
    """ """

# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from redturtle.prenotazioni import _


class IBookingType(model.Schema):
    """Marker interface and Dexterity Python Schema for Prenotazione"""

    duration = schema.Choice(
        title=_("Duration value"),
        required=True,
        vocabulary="redturtle.prenotazioni.VocDurataIncontro",
    )

    requirements = RichText(
        required=False,
        title=_("Cosa serve", default="Cosa serve"),
        description=_(
            "Elencare le informazioni utili per il giorno della prenotazione, come ad esempio i documenti da presentare."
        ),
    )

    gates = schema.List(
        title=_("gates_label", "Gates"),
        description=_("gates_help", default="Put gates here (one per line)."),
        required=True,
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.VocBookingTypeGates"
        ),
        default=[],
    )


@implementer(IBookingType)
class BookingType(Item):
    """ """

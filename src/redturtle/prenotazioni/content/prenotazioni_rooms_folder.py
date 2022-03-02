# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import implementer
from zope.interface import invariant

from plone.autoform import directives as form

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.content.prenotazioni_folder import PrenotazioniFolder
from redturtle.prenotazioni import _


from plone.z3cform.textlines import TextLinesFieldWidget


class IPrenotazioniRoomsFolder(IPrenotazioniFolder):
    """Marker interface and Dexterity Python Schema for PrenotazioniFolder"""

    # hide the booking_types field
    booking_types = schema.TextLine(required=False)
    form.widget(booking_types=TextLinesFieldWidget)
    form.mode(booking_types="hidden")

    booking_type = schema.TextLine(
        title=_("booking_type_label", default="Resource type"), required=True
    )

    gates = schema.List(
        title=_("rooms_label", "Rooms"),
        description=_("rooms_help", default="Put rooms here (one per line)."),
        required=True,
        value_type=schema.TextLine(),
        default=[],
    )

    @invariant
    def data_validation(data):
        # modification of prenotazioni_folder.IPrenotazioniFolder.data_validation
        value = data.booking_types
        data.booking_types = [{"name": value, "duration": "0"}]
        pass


@implementer(IPrenotazioniRoomsFolder)
class PrenotazioniRoomsFolder(PrenotazioniFolder):
    """ """

    @property
    def booking_types(self):
        """ """
        return [
            {"name": self.booking_type, "duration": "0"},
        ]

    @booking_types.setter
    def booking_types(self, value):
        """ """
        pass

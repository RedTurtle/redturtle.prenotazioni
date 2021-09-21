# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import invariant

from plone.autoform import directives as form

from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.content.prenotazioni_folder import PrenotazioniFolder
from redturtle.prenotazioni import _

from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow

from plone.z3cform.textlines import TextLinesFieldWidget


class IPrenotazioniRoomsFolder(IPrenotazioniFolder):
    """ Marker interface and Dexterity Python Schema for PrenotazioniFolder
    """

    # hide the booking_types field
    booking_types = schema.TextLine(required=False)
    form.widget(booking_types=TextLinesFieldWidget)
    form.mode(booking_types='hidden')

    gates = schema.List(
        title=_("rooms_label", "Rooms"),
        description=_(
            "rooms_help",
            default="Put rooms here (one per line)."
        ),
        required=True,
        value_type=schema.TextLine(),
        default=[],
    )

    @invariant
    def data_validation(data):
        ## modification of prenotazioni_folder.IPrenotazioniFolder.data_validation
        data.booking_types = [{"name":"Reserved Room", "duration":"0"}]


@implementer(IPrenotazioniRoomsFolder)
class PrenotazioniRoomsFolder(PrenotazioniFolder):
    """
    """

    @property
    def booking_types(self):
        # add gate based on context or request?

        #btypes = []
        #for g in self.gates:
            #btypes.append({"name":"Reserved Room %s"%g, "duration":"0"})
        #return btypes

        return [{"name":"Reserved Room", "duration":"0"},]

    @booking_types.setter
    def booking_types(self, value):
        return
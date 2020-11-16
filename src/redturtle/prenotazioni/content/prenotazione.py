# -*- coding: utf-8 -*-
from DateTime import DateTime
from .prenotazioni_folder import IPrenotazioniFolder
from plone.dexterity.content import Item
from plone.supermodel import model
from redturtle.prenotazioni import _
from zope import schema
from zope.interface import implementer


class IPrenotazione(model.Schema):
    """ Marker interface and Dexterity Python Schema for Prenotazione
    """

    # XXX validator
    email = schema.TextLine(title=_(u"email"))
    telefono = schema.TextLine(title=_(u"Phone number"), required=False)
    mobile = schema.TextLine(
        title=_("mobile", u"Mobile number"), required=False
    )

    tipologia_prenotazione = schema.Choice(
        title=_(u"label_typology", default="Typology"),
        vocabulary="redturtle.prenotazioni.tipologies",
    )

    # XXX visibile solo in view
    data_prenotazione = schema.Datetime(
        title=_(u"Booking date"), required=True
    )

    azienda = schema.TextLine(
        title=_(u"Company"),
        description=_(
            u"Inserisci la denominazione dell'azienda " u"del richiedente"
        ),
        required=False,
    )

    gate = schema.TextLine(
        title=_(u"Gate"), description=_(u"Sportello a cui presentarsi")
    )

    data_scadenza = schema.Datetime(
        title=_(u"Expiration date booking"), required=True
    )

    staff_notes = schema.Text(
        required=False, title=_("staff_notes_label", u"Staff notes")
    )


@implementer(IPrenotazione)
class Prenotazione(Item):
    """
    """

    def getData_prenotazione(self):
        return self.data_prenotazione

    def setData_prenotazione(self, date):
        self.data_prenotazione = date
        return

    def getData_scadenza(self):
        return self.data_scadenza

    def setData_scadenza(self, date):
        self.data_scadenza = date
        return

    def getTipologia_prenotazione(self):
        return self.tipologia_prenotazione

    def getAzienda(self):
        return self.azienda

    def getMobile(self):
        return self.mobile

    def getTelefono(self):
        return self.telefono

    def getEmail(self):
        return self.email

    def getStaff_notes(self):
        return self.staff_notes

    def getPrenotazioniFolder(self):
        """Ritorna l'oggetto prenotazioni folder"""

        for parent in self.aq_chain:
            if IPrenotazioniFolder.providedBy(parent):
                return parent
        raise Exception(
            "Could not find Prenotazioni Folder "
            "in acquisition chain of %r" % self
        )

    def getDuration(self):
        """ Return current duration
        """
        start = self.getData_prenotazione()
        end = self.getData_scadenza()
        if start and end:
            return end - start
        else:
            return 1

    def Subject(self):
        """ Reuse plone subject to do something useful
        """
        return ""

    def Date(self):
        """
        Dublin Core element - default date
        """
        # Return reservation date
        return DateTime(self.getData_prenotazione())

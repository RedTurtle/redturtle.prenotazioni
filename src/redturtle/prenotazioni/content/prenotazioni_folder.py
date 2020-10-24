# -*- coding: utf-8 -*-
from collective import dexteritytextindexer
from collective.z3cform.datagridfield import BlockDataGridFieldFactory
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.namedfile import field as namedfile
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from redturtle.prenotazioni import _
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.textlines import TextLinesFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Interface


from datetime import date
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class ISettimanaTipoRow(model.Schema):

    giorno = schema.TextLine(title=_(u"Giorno"), required=False)
    inizio_m = schema.Choice(
        title=_(u"Ora inizio mattina"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )
    end_m = schema.Choice(
        title=_(u"Ora fine mattina"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )

    inizio_p = schema.Choice(
        title=_(u"Ora inizio pomeriggio"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )

    end_p = schema.Choice(
        title=_(u"Ora fine pomeriggio"),
        vocabulary="redturtle.prenotazioni.VocOreInizio",
        required=False,
    )


class ITipologiaRow(Interface):
    name = schema.TextLine(title=_(u"Typology name"), required=True,)
    duration = schema.Choice(
        title=_(u"Duration value"),
        required=True,
        vocabulary="redturtle.prenotazioni.VocDurataIncontro",
    )


class IPrenotazioniFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for PrenotazioniFolder
    """

    dexteritytextindexer.searchable("descriptionAgenda")
    descriptionAgenda = RichText(
        required=False,
        title=_(u"Descrizione Agenda", default=u"Descrizione Agenda"),
        description=(u"Inserire il testo di presentazione " u"dell'agenda corrente"),
    )

    directives.widget(required_booking_fields=CheckBoxFieldWidget)
    required_booking_fields = schema.List(
        title=_("label_required_booking_fields", default=u"Required booking fields"),
        description=_(
            "help_required_booking_fields",
            u"User will not be able to add a booking unless those "
            u"fields are filled. "
            u"Remember that, "
            u"whatever you selected in this list, "
            u"users have to supply at least one "
            u'of "Email", "Mobile", or "Telephone"',
        ),
        required=False,
        value_type=schema.Choice(
            vocabulary="redturtle.prenotazioni.requirable_booking_fields"
        ),
    )

    daData = schema.Date(title=_(u"Data inizio validità"),)

    aData = schema.Date(
        title=_(u"Data fine validità"),
        description=_(
            "aData_help",
            default=u"Leave empty, and this Booking Folder will never expire",
        ),  # noqa
        required=False,
    )

    def get_options():
        """ Return the options for this widget
        """
        today = date.today().strftime("%Y/%m/%d")
        options = [
            SimpleTerm(value="yes", token="yes", title=_(u"Yes"),),
            SimpleTerm(value="no", token="no", title=_(u"No"),),
            SimpleTerm(value=today, token=today, title=_(u"No, just for today"),),
        ]

        return SimpleVocabulary(options)

    same_day_booking_disallowed = schema.Choice(
        title=_("label_required_booking_fields", default=u"Required booking fields"),
        description=_(
            "help_same_day_booking_disallowed",
            u"States if it is not allowed to reserve a booking "
            u"during the current day",
        ),
        required=True,
        source=get_options(),
    )

    settimana_tipo = schema.List(
        title=_(u"Settimana Tipo"),
        description=_(u"Indicare la composizione della settimana tipo"),
        required=True,
        value_type=DictRow(schema=ISettimanaTipoRow),
        default=[
            {
                "giorno": u"Lunedì",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Martedì",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Mercoledì",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Giovedì",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Venerdì",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Sabato",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
            {
                "giorno": u"Domenica",
                "inizio_m": None,
                "inizio_p": None,
                "end_m": None,
                "end_p": None,
            },
        ],
    )
    form.widget(settimana_tipo=DataGridFieldFactory)

    festivi = schema.List(
        title=_(u"Giorni festivi"),
        description=_(
            "help_holidays",
            u"Indicare i giorni festivi (uno per riga) "
            u"nel formato GG/MM/AAAA. Al posto dell'anno puoi mettere un "
            u"asterisco per indicare un evento che ricorre annualmente.",
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[],
    )

    futureDays = schema.Int(
        default=0,
        title=_(u"Max days in the future"),
        description=_(
            "futureDays",
            default=u"Limit booking in the future to an amount "
            u"of days in the future starting from "
            u"the current day. \n"
            u"Keep 0 to give no limits.",
        ),
    )

    notBeforeDays = schema.Int(
        default=2,
        title=_(u"Days booking is not allowed before"),
        description=_(
            "notBeforeDays",
            default=u"Booking is not allowed before the amount "
            u"of days specified. \n"
            u"Keep 0 to give no limits.",
        ),
    )

    tipologia = schema.List(
        title=_(u"Tipologie di richiesta"),
        description=_(
            "tipologia_help",
            default=u"Put booking types there (one per line).\n"
            u"If you do not provide this field, "
            u"not type selection will be available",
        ),
        value_type=DictRow(schema=ITipologiaRow),
    )
    form.widget(tipologia=DataGridFieldFactory)

    gates = schema.List(
        title=_("gates_label", "Gates"),
        description=_(
            "gates_help",
            default=u"Put gates here (one per line). "
            u"If you do not fill this field, "
            u"one gate is assumed",
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[],
    )

    unavailable_gates = schema.List(
        title=_("unavailable_gates_label", "Unavailable gates"),
        description=_(
            "unavailable_gates_help",
            default=u"Add a gate here (one per line) if, "
            u"for some reason, "
            u"it is not be available."
            u"The specified gate will not be taken in to "  # noqa
            u"account for slot allocation. "
            u"Each line should match a corresponding "
            u'line in the "Gates" field',
        ),
        required=False,
        value_type=schema.TextLine(),
        default=[],
    )

    # XXX validate email
    email_responsabile = schema.TextLine(
        title=_(u"Email del responsabile"),
        description=_(
            u"Inserisci l'indirizzo email del responsabile " "delle prenotazioni"
        ),
        required=False,
    )


@implementer(IPrenotazioniFolder)
class PrenotazioniFolder(Container):
    """
    """

    def getDescriptionAgenda(self):
        return self.descriptionAgenda

    def getSettimana_tipo(self):
        return self.settimana_tipo

    def getGates(self):
        return self.gates

    def getUnavailable_gates(self):
        return self.unavailable_gates

    def getDaData(self):
        return self.daData

    def getAData(self):
        return self.aData

    def getTipologia(self):
        return self.tipologia

    def getFestivi(self):
        return self.festivi

    def getFutureDays(self):
        return self.futureDays

    def getNotBeforeDays(self):
        return self.notBeforeDays

# -*- coding: utf-8 -*-
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider

from redturtle.prenotazioni import _


@provider(IFormFieldProvider)
class IContacts(model.Schema):
    """ """

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
        label=_("contacts_label", default="Contacts"),
        description=_(
            "contacts_help",
            default="Show here contacts information that will be used by authomatic mail system",  # noqa
        ),
        fields=["how_to_get_here", "phone", "fax", "pec", "complete_address"],
    )


@implementer(IContacts)
@adapter(IDexterityContent)
class Contacts(object):
    """ """

    def __init__(self, context):
        self.context = context

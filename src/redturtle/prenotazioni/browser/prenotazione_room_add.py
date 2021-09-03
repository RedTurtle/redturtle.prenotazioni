# -*- coding: utf-8 -*-

from Acquisition import aq_inner

from datetime import datetime
from datetime import timedelta

from DateTime import DateTime

from six.moves.urllib.parse import urlparse, parse_qs

from email.utils import formataddr
from email.utils import parseaddr
from os import environ
from plone import api
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from plone.z3cform.layout import wrap_form
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import IBooker

from plone.formwidget.recaptcha.widget import ReCaptchaFieldWidget

from redturtle.prenotazioni.browser.z3c_custom_widget import (
    CustomRadioFieldWidget,
)

#from redturtle.prenotazioni.utilities.urls import urlify
from redturtle.prenotazioni.browser.prenotazione_add import IAddForm, AddForm, check_is_future_date

from z3c.form.interfaces import HIDDEN_MODE, DISPLAY_MODE, INPUT_MODE

from zope.component import getUtility
from zope.interface import implementer
from z3c.form import field

#from zope.interface import Interface
#from zope.interface import Invalid
from zope.schema import Choice
from zope.schema import Datetime
#from zope.schema import Text
#from zope.schema import TextLine
from zope.schema import ValidationError
#from zope.annotation.interfaces import IAnnotations
#from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from zope.schema.interfaces import IVocabularyFactory
#import re
#import six



class IAddRoomForm(IAddForm):

    """
    Interface for creating a prenotazione of room
    """

    ending_booking_date = Datetime(
        title=_("label_ending_booking_time", u"Ending Booking time"),
        default=None,
        constraint=check_is_future_date,
        required=True
    )


@implementer(IAddRoomForm)
class AddRoomForm(AddForm):
    """
    """

    render_form = False
    ignoreContext = True

    @property
    def fields(self):
        fields = field.Fields(IAddRoomForm)
        fields["captcha"].widgetFactory = ReCaptchaFieldWidget
        fields["tipology"].widgetFactory = CustomRadioFieldWidget
        if api.user.is_anonymous():
            return fields
        return fields.omit("captcha")

    def updateWidgets(self):
        super(AddRoomForm, self).updateWidgets()

        #self.widgets["tipology"].mode = DISPLAY_MODE
        self.widgets["tipology"].value = "Reserved Room"

        bookingdate = self.widgets["booking_date"].value
        start_date = datetime.strptime(bookingdate, '%Y-%m-%d %H:%M')
        end_date = start_date + timedelta(hours=1)
        self.widgets["ending_booking_date"].value = end_date.strftime('%Y-%m-%d %H:%M')

    def do_book(self, data):
        """
        Create a Booking!
        """
        booker = IBooker(self.context.aq_inner)
        referer = self.request.get("HTTP_REFERER", None)
        duration_delta = data["ending_booking_date"] - data["booking_date"]
        duration = duration_delta.seconds / (60 * 60 * 24)
        if referer:
            parsed_url = urlparse(referer)
            params = parse_qs(parsed_url.query)
            if "gate" in params:
                return booker.create(data, duration=duration, force_gate=params["gate"][0])
        return booker.create(data, duration=duration)


WrappedAddForm = wrap_form(AddRoomForm)

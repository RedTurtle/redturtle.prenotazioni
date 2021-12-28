# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from email.utils import formataddr
from email.utils import parseaddr
from os import environ
from plone import api
from plone.formwidget.recaptcha.widget import ReCaptchaFieldWidget
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from plone.z3cform.layout import wrap_form
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from redturtle.prenotazioni import _
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import IBooker

# from redturtle.prenotazioni.utilities.urls import urlify
from redturtle.prenotazioni.browser.prenotazione_add import AddForm
from redturtle.prenotazioni.browser.prenotazione_add import check_is_future_date
from redturtle.prenotazioni.browser.prenotazione_add import IAddForm

# from redturtle.prenotazioni.browser.prenotazione_add import prenotazioni
from redturtle.prenotazioni.browser.z3c_custom_widget import CustomRadioFieldWidget
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.parse import urlparse
from z3c.form import field
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import INPUT_MODE
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Invalid

# from zope.schema import Text
# from zope.schema import TextLine
# from zope.interface import Interface
# from zope.interface import Invalid
from zope.schema import Choice
from zope.schema import Datetime
from zope.schema import ValidationError

# from zope.annotation.interfaces import IAnnotations
# from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from zope.schema.interfaces import IVocabularyFactory


# import re
# import six


class IAddRoomForm(IAddForm):

    """
    Interface for creating a prenotazione of room
    """

    ending_booking_date = Datetime(
        title=_("label_ending_booking_time", u"Ending Booking time"),
        default=None,
        constraint=check_is_future_date,
        required=True,
    )


@implementer(IAddRoomForm)
class AddRoomForm(AddForm):
    """ """

    render_form = False
    ignoreContext = True

    @property
    def fields(self):
        fields = field.Fields(IAddRoomForm)
        fields["captcha"].widgetFactory = ReCaptchaFieldWidget
        if api.user.is_anonymous():
            return fields
        return fields.omit("captcha")

    def updateWidgets(self):
        super(AddRoomForm, self).updateWidgets()

        self.widgets["tipology"].mode = HIDDEN_MODE
        value = self.context.booking_type
        self.widgets["tipology"].value = value

        bookingdate = self.widgets["booking_date"].value
        start_date = datetime.strptime(bookingdate, "%Y-%m-%d %H:%M")
        end_date = start_date + timedelta(hours=1)
        self.widgets["ending_booking_date"].value = end_date.strftime("%Y-%m-%d %H:%M")

    def do_book(self, data):
        """
        Create a Booking!
        """
        booker = IBooker(self.context.aq_inner)
        referer = self.request.get("HTTP_REFERER", None)
        duration_delta = data["ending_booking_date"] - data["booking_date"]
        duration = duration_delta.seconds / (60 * 60 * 24)

        conflict_manager = self.prenotazioni.conflict_manager

        slot = conflict_manager.get_choosen_slot(data)
        prenotazioni = self.context.restrictedTraverse("@@prenotazioni_context_state")

        if prenotazioni.is_slot_busy(data["booking_date"], slot):
            msg = _(u"Sorry, this slot is not available anymore.")
            raise WidgetActionExecutionError("booking_date", Invalid(msg))

        if referer:
            parsed_url = urlparse(referer)
            params = parse_qs(parsed_url.query)
            if "gate" in params:
                return booker.create(
                    data, duration=duration, force_gate=params["gate"][0]
                )
        return booker.create(data, duration=duration)


WrappedAddForm = wrap_form(AddRoomForm)

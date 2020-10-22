# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from plone import api
from plone.formwidget.recaptcha.widget import ReCaptchaFieldWidget
from plone.memoize.view import memoize
from plone.z3cform.layout import wrap_form
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from redturtle.prenotazioni import _
from redturtle.prenotazioni import TZ
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.browser.z3c_custom_widget import CustomRadioFieldWidget
from redturtle.prenotazioni.utilities.urls import urlify
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import ActionExecutionError
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getMultiAdapter
from zope.component._api import getUtility
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import Choice
from zope.schema import Datetime
from zope.schema import Text
from zope.schema import TextLine
from zope.schema import ValidationError

import pytz
import re
import six


TELEPHONE_PATTERN = re.compile(r'^(\+){0,1}([0-9]| )*$')


class InvalidPhone(ValidationError):
    __doc__ = _('invalid_phone_number', u"Invalid phone number")


class InvalidEmailAddress(ValidationError):
    __doc__ = _('invalid_email_address', u"Invalid email address")


class IsNotfutureDate(ValidationError):
    __doc__ = _('is_not_future_date', u"This date is past")


def check_phone_number(value):
    '''
    If value exist it should match TELEPHONE_PATTERN
    '''
    if not value:
        return True
    if isinstance(value, six.string_types):
        value = value.strip()
    if TELEPHONE_PATTERN.match(value) is not None:
        return True
    raise InvalidPhone(value)


def check_valid_email(value):
    '''Check if value is a valid email address'''
    if not value:
        return True
    portal = getUtility(ISiteRoot)

    reg_tool = getToolByName(portal, 'portal_registration')
    if value and reg_tool.isValidEmail(value):
        return True
    else:
        raise InvalidEmailAddress


def check_is_future_date(value):
    '''
    Check if this date is in the future
    '''
    if not value:
        return True

    now = tznow()

    if isinstance(value, datetime) and value >= now:
        return True
    raise IsNotfutureDate


class IAddForm(Interface):

    """
    Interface for creating a prenotazione
    """
    booking_date = Datetime(
        title=_('label_booking_time', u'Booking time'),
        default=None,
        constraint=check_is_future_date,
    )
    tipology = Choice(
        title=_('label_tipology', u'Tipology'),
        required=True,
        default=u'',
        vocabulary='redturtle.prenotazioni.tipologies',
    )
    fullname = TextLine(
        title=_('label_fullname', u'Fullname'),
        default=u'',
    )
    email = TextLine(
        title=_('label_email', u'Email'),
        required=True,
        default=u'',
        constraint=check_valid_email,
    )
    phone = TextLine(
        title=_('label_phone', u'Phone number'),
        required=False,
        default=u'',
        constraint=check_phone_number,
    )
    mobile = TextLine(
        title=_('label_mobile', u'Mobile number'),
        required=False,
        default=u'',
        constraint=check_phone_number,
    )
    subject = Text(
        title=_('label_subject', u'Subject'),
        default=u'',
        required=False,
    )
    agency = TextLine(
        title=_('label_agency', u'Agency'),
        description=_('description_agency',
                      u'If you work for an agency please specify its name'),
        default=u'',
        required=False,
    )
    captcha = TextLine(
        title=u" ",
        description=u"",
        required=False
    )


@implementer(IAddForm)
class AddForm(form.AddForm):
    """
    """

    render_form = False
    ignoreContext = True

    @property
    def fields(self):
        fields = field.Fields(IAddForm)
        fields['captcha'].widgetFactory = ReCaptchaFieldWidget
        fields['tipology'].widgetFactory = CustomRadioFieldWidget
        if api.user.is_anonymous():
            return fields
        return fields.omit('captcha')

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['booking_date'].mode = HIDDEN_MODE
        bookingdate = self.request.form.get(
            'form.booking_date',
            self.request.form.get('form.widgets.booking_date')
        )
        self.widgets['booking_date'].value = bookingdate

        if self.widgets['agency'].__name__ in self.context.required_booking_fields:
            self.widgets['agency'].required = True
        if self.widgets['email'].__name__ in self.context.required_booking_fields:
            self.widgets['email'].required = True
        if self.widgets['mobile'].__name__ in self.context.required_booking_fields:
            self.widgets['mobile'].required = True
        if self.widgets['phone'].__name__ in self.context.required_booking_fields:
            self.widgets['phone'].required = True

    @property
    @memoize
    def localized_time(self):
        ''' Facade for context/@@plone/toLocalizedTime
        '''
        return api.content.get_view('plone',
                                    self.context,
                                    self.request).toLocalizedTime

    @property
    @memoize
    def label(self):
        '''
        Check if user is anonymous
        '''
        booking_date = self.booking_DateTime
        if not booking_date:
            return ''
        localized_date = self.localized_time(booking_date)
        return _('label_selected_date',
                 u"Selected date: ${date} — Time slot: ${slot}",
                 mapping={'date': localized_date,
                          'slot': booking_date.hour()})

    @property
    @memoize
    def description(self):
        '''
        Check if user is anonymous
        '''
        return _('help_prenotazione_add', u"")

    @property
    @memoize
    def booking_DateTime(self):
        ''' Return the booking_date as passed in the request as a DateTime
        object
        '''
        booking_date = self.request.form.get('form.booking_date', None)
        # BBB Adapt to z3c without change a lot the code
        if not booking_date:
            booking_date = self.request.form.get('form.widgets.booking_date', None)

        if not booking_date:
            return None

        if len(booking_date) == 16:
            if TZ._tzname == 'RMT':
                tzname = 'CEST'
            else:
                tzname = TZ._tzname

            booking_date = ' '.join((booking_date, tzname))
        return DateTime(booking_date)

    @property
    @memoize
    def is_anonymous(self):
        '''
        Check if user is anonymous
        '''
        return api.content.get_view('plone_portal_state',
                                    self.context,
                                    self.request).anonymous()

    @property
    @memoize
    def prenotazioni(self):
        ''' Returns the prenotazioni_context_state view.

        Everyone should know about this!
        '''
        return api.content.get_view('prenotazioni_context_state',
                                    self.context,
                                    self.request)

    def do_book(self, data):
        '''
        Create a Booking!
        '''
        booker = IBooker(self.context.aq_inner)
        return booker.create(data)

    @property
    @memoize
    def back_to_booking_url(self):
        ''' This goes back to booking view.
        '''
        params = self.prenotazioni.remembered_params.copy()
        b_date = self.booking_DateTime
        if b_date:
            params['data'] = b_date.strftime('%d/%m/%Y')
        target = urlify(self.context.absolute_url(), params=params)
        return target

    def exceedes_date_limit(self, data):
        '''
        Check if we can book this slot or is it too much in the future.
        '''
        future_days = self.context.getFutureDays()
        if not future_days:
            return False
        booking_date = data.get('booking_date', None)
        if not isinstance(booking_date, datetime):
            return False
        date_limit = tznow() + timedelta(future_days)
        if not booking_date.tzinfo:
            tzinfo = date_limit.tzinfo
            booking_date = tzinfo.localize(booking_date)

        if booking_date <= date_limit:
            return False
        return True


    @button.buttonAndHandler(_(u'action_book', u'Book'))
    def action_book(self, action):
        '''
        Book this resource
        '''
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        if not data.get('booking_date'):
            raise WidgetActionExecutionError(
                'booking_date',
                Invalid(_(u"Please provide a booking date"))
            )

        conflict_manager = self.prenotazioni.conflict_manager
        if conflict_manager.conflicts(data):
            msg = _(u'Sorry, this slot is not available anymore.')
            raise WidgetActionExecutionError(
                'booking_date',
                Invalid(msg)
            )
        if self.exceedes_date_limit(data):
            msg = _(u'Sorry, you can not book this slot for now.')
            raise WidgetActionExecutionError(
                'booking_date',
                Invalid(msg)
            )

        captcha = getMultiAdapter(
            (aq_inner(self.context), self.request),
            name='recaptcha'
        )

        if 'captcha' in data and not captcha.verify():
            msg=_(u"Please check the captcha")
            raise ActionExecutionError(Invalid(msg))

        obj = self.do_book(data)
        if not obj:
            msg = _(u'Sorry, this slot is not available anymore.')
            api.portal.show_message(
                message=msg,
                type='warning',
                request=self.request)
            target = self.back_to_booking_url
            return self.request.response.redirect(target)
        msg = _('booking_created')
        api.portal.show_message(message=msg, type='info', request=self.request)
        booking_date = data['booking_date'].strftime('%d/%m/%Y')
        params = {'data': booking_date,
                  'uid': obj.UID()}
        target = urlify(self.context.absolute_url(),
                        paths=["@@prenotazione_print"],
                        params=params)
        return self.request.response.redirect(target)

    @button.buttonAndHandler(_(u"action_cancel", default=u"Cancel"), name='cancel')
    def action_cancel(self, action):
        '''
        Cancel
        '''
        target = self.back_to_booking_url
        return self.request.response.redirect(target)

    def show_message(self, msg, msg_type):
        ''' Facade for the show message api function
        '''
        show_message = api.portal.show_message
        return show_message(msg, request=self.request, type=msg_type)

    def redirect(self, target, msg="", msg_type="error"):
        """ Redirects the user to the target, optionally with a portal message
        """
        if msg:
            self.show_message(msg, msg_type)
        return self.request.response.redirect(target)

    def has_enough_time(self):
        """ Check if we have enough time to book something
        """
        booking_date = self.booking_DateTime.asdatetime()
        return self.prenotazioni.is_booking_date_bookable(booking_date)

    def __call__(self):
        ''' Redirects to the context if no data is found in the request
        '''
        # we should always have a booking date
        if not self.booking_DateTime:
            msg = _('please_pick_a_date', "Please select a time slot")
            return self.redirect(self.back_to_booking_url, msg)
        # and if we have it, we should have enough time to do something
        if not self.has_enough_time():
            msg = _('time_slot_to_short',
                    "You cannot book any typology at this time")
            return self.redirect(self.back_to_booking_url, msg)
        return super(AddForm, self).__call__()

WrappedAddForm = wrap_form(AddForm)

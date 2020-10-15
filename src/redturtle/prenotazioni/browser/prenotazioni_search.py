# -*- coding: utf-8 -*-
from datetime import datetime
from DateTime import DateTime
# from five.formlib.formbase import PageForm
from plone import api
from plone.memoize.view import memoize
from plone.z3cform.layout import wrap_form
from Products.CMFPlone import PloneMessageFactory as __
# from plone.app.form.validators import null_validator
from Products.CMFPlone.browser.search import quote_chars
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.conflict import IConflictManager
# from zope.formlib.form import setUpWidgets
from z3c.form import button
from z3c.form import field
from z3c.form import form
# from zope.formlib.form import FormFields, action
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import Choice
from zope.schema import Date
from zope.schema import TextLine
from zope.schema import ValidationError


class InvalidDate(ValidationError):
    __doc__ = _('invalid_end:search_date', u"Invalid start or end date")


class ISearchForm(Interface):
    """
    Interface for creating a prenotazione
    """
    text = TextLine(
        title=_('label_text', u'Text to search'),
        default=u'',
        required=False,
    )
    review_state = Choice(
        title=__("State"),
        default='',
        required=False,
        source='redturtle.prenotazioni.booking_review_states'
    )
    gate = Choice(
        title=_("label_gate", u"Gate"),
        default='',
        required=False,
        source='redturtle.prenotazioni.gates'
    )
    start = Date(
        title=_('label_start', u'Start date '),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )
    end = Date(
        title=_('label_end', u'End date'),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        required=False,
    )


@implementer(ISearchForm)
class SearchForm(form.Form):

    """
    """
    ignoreContext = True
    template = ViewPageTemplateFile('templates/prenotazioni_search.pt')
    prefix = ''
    brains = []


    fields = field.Fields(ISearchForm)

    @property
    @memoize
    def conflict_manager(self):
        '''
        Return the conflict manager for this context
        '''
        return IConflictManager(self.context)

    @property
    @memoize
    def prenotazioni_week_view(self):
        '''
        Return the conflict manager for this context
        '''
        return api.content.get_view('prenotazioni_week_view',
                                    self.context,
                                    self.request)

    def get_query(self, data):
        ''' The query we requested
        '''
        query = {
            'sort_on': 'Date',
            'sort_order': 'reverse',
            'path': '/'.join(self.context.getPhysicalPath())
        }
        if data.get('text'):
            query['SearchableText'] = quote_chars(data['text'].encode('utf8'))
        if data.get('review_state'):
            query['review_state'] = data['review_state']

        if data.get('gate'):
            query['Subject'] = "Gate: %s" % data['gate'].encode('utf8')

        start = data['start']
        end = data['end']
        if start and end:
            query['Date'] = {'query': [DateTime(start.__str__()), DateTime(end.__str__()) + 1],
                             'range': 'min:max'}
        elif start:
            query['Date'] = {'query': DateTime(start.__str__()), 'range': 'min'}
        elif end:
            query['Date'] = {'query': DateTime(end.__str__()) + 1, 'range': 'max'}
        return query

    def get_brains(self, data):
        '''
        The brains for my search
        '''
        if not self.request.form.get('buttons.action_search'):
            return []
        query = self.get_query(data)
        return self.conflict_manager.unrestricted_prenotazioni(**query)

    # Use base form validation
    # def validate(self, action, data):
    #     '''
    #     Checks if input dates are correct
    #     '''
    #     errors = super(SearchForm, self).validate(action, data)
    #     return errors

    def setUpWidgets(self, ignore_request=False):
        '''
        From zope.formlib.form.Formbase.
        '''
        self.adapters = {}
        fieldnames = [x.__name__ for x in self.form_fields]
        data = {}
        for key in fieldnames:
            form_value = self.request.form.get(key)
            if form_value is not None and not form_value == u'':
                field = self.form_fields[key].field
                if isinstance(field, Choice):
                    try:
                        data[key] = (field.bind(self.context).vocabulary
                                     .getTermByToken(form_value).value)
                    except LookupError:
                        data[key] = form_value
                else:
                    data[key] = form_value
                self.request[key] = form_value

        self.widgets = setUpWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            form=self, adapters=self.adapters, ignore_request=ignore_request,
            data=data)
        self.widgets['gate']._messageNoValue = ""
        self.widgets['review_state']._messageNoValue = ""

    @button.buttonAndHandler(_(u"action_search", default=u"Search"))
    def action_search(self, action):
        '''
        Search in prenotazioni SearchableText
        '''
        data, errors = self.extractData()
        self.brains = self.get_brains(data)

    @button.buttonAndHandler(_(u"action_cancel", default=u"Cancel"))
    def action_cancel(self, action):
        '''
        Cancel and go back to the week view
        '''
        target = self.context.absolute_url()
        return self.request.response.redirect(target)

WrappedSearchForm = wrap_form(SearchForm)

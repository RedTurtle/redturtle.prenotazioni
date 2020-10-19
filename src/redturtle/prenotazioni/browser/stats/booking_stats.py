# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOTreeSet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from io import StringIO
#from cStringIO import StringIO
from csv import writer
from datetime import date, datetime, timedelta
from five.formlib.formbase import PageForm
from json import dumps, loads
from redturtle.prenotazioni import prenotazioniFileLogger
from redturtle.prenotazioni import prenotazioniLogger as logger
from redturtle.prenotazioni import _
from plone import api
from plone.app.form.validators import null_validator
from plone.memoize.view import memoize
from plone.memoize.view import memoize_contextless
from redturtle.prenotazioni.browser.base import BaseView as PrenotazioniBaseView
from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from redturtle.prenotazioni.utilities.urls import urlify
from time import mktime
from zope.annotation.interfaces import IAnnotations
from zope.formlib.form import FormFields, action, setUpWidgets
from zope.interface import implementer, Interface
from zope.schema import Date, TextLine, ValidationError
import six
from six.moves import map


class InvalidDate(ValidationError):
    __doc__ = _('invalid_end:search_date', u"Invalid start or end date")


def check_date(value):
    '''
    Check if the input date is correct
    '''
    if isinstance(value, date):
        return True
    raise InvalidDate


class IQueryForm(Interface):
    """
    Interface for querying stuff
    """
    user = TextLine(
        title=_(u'label_user', "User"),
        default=u'',
        required=False
    )
    start = Date(
        title=_('label_start', u'Start date '),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        constraint=check_date,
        required=False,
    )
    end = Date(
        title=_('label_end', u'End date'),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        constraint=check_date,
        required=False,
    )


def date2timestamp(value, delta=0):
    ''' Conerts a date in the format "%Y-%m-%d" to a unix timestamp
    '''
    try:
        value = datetime.strptime(value, "%Y-%m-%d")
        value = value + timedelta(delta)
        return mktime(value.timetuple())
    except Exception as e:
        logger.exception(value)
        raise(e)


def timestamp2date(value, date_format='%Y/%m/%d %H:%M'):
    ''' Converts a timestamp to date_format
    '''
    return datetime.fromtimestamp(value).strftime(date_format)


@implementer(IQueryForm)
class BaseForm(PageForm):
    ''' The base class for this context
    '''
    resetForm = False
    entry_set = set([])
    # entry indexes:
    _ei_action = 0
    _ei_date = 2
    _ei_user = 6
    template = ViewPageTemplateFile('booking_stats.pt')

    def set_header(self, *args):
        '''
        Shorcut for setting headers in the request
        '''
        return self.request.RESPONSE.setHeader(*args)

    @property
    @memoize_contextless
    def start_timestamp(self):
        """ Returns the timestamp of the parameter in the request
        """
        value = self.request.form.get('form.start', '1970-01-01')
        try:
            return date2timestamp(value)
        except:
            return 0

    @property
    @memoize_contextless
    def end_timestamp(self):
        """ Returns the timestamp of the parameter in the request
        """
        value = self.request.form.get('form.end', '2037-11-20')
        try:
            return date2timestamp(value, delta=1)
        except:
            return 9999999999.0

    @property
    def user(self):
        """ Returns the user parameter in the request
        """
        return self.request.form.get('form.user', '')

    @property
    @memoize
    def form_fields(self):
        '''
        The fields for this form
        '''
        ff = FormFields(IQueryForm)
        return ff

    @property
    @memoize
    def booking_stats(self):
        ''' Return the booking_stats view
        '''
        return api.content.get_view(
            'booking_stats',
            self.context,
            self.request,
        )

    def redirect(self, target="", message="", message_type="info"):
        """ Redirect to target or context
        """
        if not target:
            target = self.context.absolute_url()
        if message:
            api.portal.show_message(
                message=message,
                request=self.request,
                type=message_type
            )
        return self.request.response.redirect(target)

    def setUpWidgets(self, ignore_request=False):
        '''
        From zope.formlib.form.Formbase.
        '''
        self.adapters = {}
        ff = self.form_fields
        fieldnames = [x.__name__ for x in ff]
        data = {}
        for key in fieldnames:
            form_value = self.request.form.get(key)
            if form_value is not None and not form_value == u'':
                data[key] = form_value
                self.request[key] = form_value

        today = date.today()
        if not ff['start'].field.default:
            ff['start'].field.default = (today - timedelta(365))
        if not ff['end'].field.default:
            ff['end'].field.default = (today)

        self.widgets = setUpWidgets(
            ff,
            self.prefix,
            self.context,
            self.request,
            form=self,
            adapters=self.adapters,
            ignore_request=ignore_request,
            data=data
        )

    def do_search(self, data):
        ''' Actually execute stuff
        '''
        return self.template()

    @action(_('action_search', u'Search'), name=u'search')
    def action_search(self, action, data):
        '''
        Do something
        '''
        return self.do_search(data)

    @action(_('action_csv', u'CSV'), name=u'csv')
    def action_csv(self, action, data):
        '''
        Do something
        '''
        return self.get_csv()

    @action(_(u"action_cancel", u"Cancel"), validator=null_validator, name=u'cancel')  # noqa
    def action_cancel(self, action, data):
        '''
        Cancel
        '''
        target = self.context.absolute_url()
        return self.redirect(target)

    def extra_script(self):
        ''' The scripts needed for the dateinput
        '''
        view = api.content.get_view(
            'rg.prenotazioni.dateinput.conf.js',
            self.context,
            self.request,
        )
        return view.render() + view.mark_with_class([r'#form\\.start', r'#form\\.end', ])  # noqa

    @property
    @memoize
    def csv_url(self):
        ''' The CSV url to get those data
        '''
        params = {
            'form.actions.csv': 1,
            'form.start': self.request.form['form.start'],
            'form.end': self.request.form['form.end'],
            'form.user': self.request.form['form.user'],
        }
        return urlify(self.context.absolute_url(), [self.__name__], params)

    @property
    @memoize
    def csv_filename(self):
        ''' The CSV filename
        '''
        return '%s-%s.csv' % (
            self.context.getId(),
            datetime.now().strftime('%Y%m%d%H%M')
        )

    @memoize_contextless
    def uid_to_url(self, uid):
        ''' Converts a uid to an url
        '''
        pc = api.portal.get_tool('portal_catalog')
        brains = pc(UID=uid)
        if not brains:
            return {
                'title': uid,
                'url': ''
            }
        brain = brains[0]
        return {
            'title': brain.Title,
            'url': brain.getURL()
        }

    @property
    @memoize
    def entry_number(self):
        ''' Number of entries
        '''
        return len(self.entry_set)

    @memoize
    def load_entries(self, resul_type='list'):
        ''' Number of entries
        '''
        return list(map(loads, self.entry_set))

    @property
    @memoize
    def older_entry(self):
        ''' The entries grouped by date
        '''
        entries = self.load_entries()
        if not entries:
            return ''
        return min(
            self.load_entries(),
            key=lambda x: x[self._ei_date]
        )

    def entries_by_action(self):
        ''' Return the entries grouped by action
        '''
        results = {}
        entries = self.load_entries()
        for entry in entries:
            results.setdefault(entry[self._ei_action], []).append(entry)
        return results

    def csvencode(self, data, human_readable=False):
        '''
        Converts an array of info to a proper cvs string

        If human_readable is set to True it will convert
        timestamps and uids
        '''
        dummy_file = StringIO()
        cw = writer(dummy_file)
        for line in data:
            if human_readable:
                line[self._ei_date] = timestamp2date(line[self._ei_date])
                line[4] = self.uid_to_url(line[4])['url']
                line.pop(3)
            for idx, value in enumerate(line):
                if isinstance(value, six.text_type):
                    line[idx] = value.encode('utf8')
            cw.writerow(line)
        return dummy_file.getvalue().strip('\r\n')

    @property
    @memoize
    def sorted_entries(self):
        ''' Return the entries as a sorted list
        '''
        return sorted(self.entry_set)

    def expand_entry(self, entry):
        ''' Expand an entry
        '''
        if isinstance(entry, six.string_types):
            entry = loads(entry)
        return {
            'action': entry[self._ei_action],
            'note': entry[1],
            'date': timestamp2date(entry[self._ei_date]),
            'agenda': self.uid_to_url(entry[3]),
            'booking': self.uid_to_url(entry[4]),
            'fullname': entry[5],
            'user': entry[self._ei_user],
        }

    def get_csv(self):
        ''' This method serves a CSV file with the data of the view
        '''
        self.set_header(
            'Content-Type', 'application/csv; charset=utf8'
        )
        self.set_header(
            'Content-Disposition',
            'attachment;filename=%s' % self.csv_filename
        )
        return self.csvencode(self.load_entries(), human_readable=True)


class ContextForm(BaseForm, PrenotazioniBaseView):
    '''
    Aggregates data from the booking folders below
    '''
    logstorage_key = 'redturtle.prenotazioni.logstorage'
    file_logger = prenotazioniFileLogger

    @property
    @memoize
    def logstorage(self):
        ''' This is an annotation OOTreeSet where we can store log entries
        '''
        annotations = IAnnotations(self.context)
        if not self.logstorage_key in annotations:
            annotations[self.logstorage_key] = OOTreeSet()
        return annotations[self.logstorage_key]

    def add_entry(self, entry):
        ''' Add an entry to the logstorage
        '''
        return self.logstorage.add(entry)

    def remove_entry(self, entry):
        ''' Remove an entry from the logstorage
        '''
        try:
            return self.logstorage.remove(entry)
        except KeyError:
            pass

    @property
    @memoize
    def entry_set(self):
        ''' All the entries saved in this object in the given time range
        '''
        if not self.prenotazioni.user_can_manage:
            return set([])
        values = set(self.logstorage)
        if not values:
            return set([])
        start = self.start_timestamp
        end = self.end_timestamp
        user = self.user
        entries = list(map(loads, self.logstorage))
        return set(
            dumps(x) for x in entries
            if (
                start < x[self._ei_date] < end
                and user in x[self._ei_user]
            )
        )

    def csvlog(self, data):
        ''' Log something, dumping it on a file and storing it in the
        logstorage
        '''
        self.file_logger.info(self.csvencode([data]))
        self.add_entry(dumps(data))


class AggregateForm(BaseForm):
    ''' The Base View to get the statistics for this site
    '''
    prenotazioni_interfaces = [
        IPrenotazioniFolder
    ]

    @property
    @memoize
    def plone_tools(self):
        ''' Proxy the plone_tools view
        '''
        return api.content.get_view('plone_tools', self.context, self.request)

    @property
    @memoize
    def prenotazioni_brains(self):
        ''' Return the prenotazioni brains under this context
        '''
        pc = self.plone_tools.catalog()
        query = {
            'object_provides': [x.__identifier__ for x in self.prenotazioni_interfaces],  # noqa
            'path': '/'.join(self.context.getPhysicalPath())
        }
        return pc(**query)

    @property
    @memoize
    def stat_views(self):
        ''' Return the views that give the statistic for all the prenotazioni
        objects
        '''
        return [
            api.content.get_view(
                'booking_stats',
                brain.getObject(),
                self.request
            ) for brain in self.prenotazioni_brains
        ]

    @property
    @memoize
    def entry_set(self):
        ''' The entry_set is the union of all the contained entry_sets
        '''
        entries = set([])
        for view in self.stat_views:
            entries = entries.union(view.entry_set)
        return entries

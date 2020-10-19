# -*- coding: utf-8 -*-
from datetime import date, timedelta
from five.formlib.formbase import PageForm
from json import loads
from pd.prenotazioni import prenotazioniMessageFactory as _
from plone import api
from plone.app.form.validators import null_validator
from plone.memoize.view import memoize
from zope.formlib.form import FormFields, action, setUpWidgets
from zope.interface import Interface
from zope.interface.declarations import implements
from zope.schema import Date


class IDeleteForm(Interface):
    delete_date = Date(
        title=_('label_delete_date', u'Delete date '),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
    )


class DeleteForm(PageForm):
    ''' View to delete the entries
    '''
    implements(IDeleteForm)

    @property
    @memoize
    def form_fields(self):
        '''
        The fields for this form
        '''
        ff = FormFields(IDeleteForm)
        ff['delete_date'].field.default = (date.today() - timedelta(100))
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
        fieldnames = [x.__name__ for x in self.form_fields]
        data = {}
        for key in fieldnames:
            form_value = self.request.form.get(key)
            if form_value is not None and not form_value == u'':
                data[key] = form_value
                self.request[key] = form_value

        self.widgets = setUpWidgets(
            self.form_fields,
            self.prefix,
            self.context,
            self.request,
            form=self,
            adapters=self.adapters,
            ignore_request=ignore_request,
            data=data
        )

    def do_delete(self, data):
        ''' Actually execute stuff
        '''
        delete_date = data['delete_date']
        delete_timestamp = int(delete_date.strftime('%s'))
        total = self.booking_stats.entry_number
        deleted = 0
        views = getattr(self.booking_stats, 'stat_views', [self.booking_stats])
        for view in views:
            for entry in view.entry_set:
                entry_obj = loads(entry)
                if delete_timestamp > entry_obj[self.booking_stats._ei_date]:
                    view.remove_entry(entry)
                    # BBB logging
                    deleted += 1
        msg = 'Deleted %s out of %s objects' % (deleted, total)
        return msg

    @action(_('action_delete', u'Delete'), name=u'delete')
    def action_delete(self, action, data):
        '''
        Do something
        '''
        msg = self.do_delete(data)
        target = '%s/%s' % (
            self.context.absolute_url(),
            self.booking_stats.__name__
        )
        return self.redirect(target, msg)

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
        return view.render() + view.mark_with_class([r'#form\\.delete_date'])

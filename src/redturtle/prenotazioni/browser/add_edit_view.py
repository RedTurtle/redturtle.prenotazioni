from collective.z3cform.datagridfield import BlockDataGridFieldFactory
from plone.dexterity.browser.add import DefaultAddForm as BaseAddForm
from plone.dexterity.browser.add import DefaultAddView as BaseAddView
from plone.dexterity.browser.edit import DefaultEditForm as BaseEdit
from plone.dexterity.events import AddCancelledEvent
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent
from plone.dexterity.i18n import MessageFactory as _dmf
from plone.dexterity.interfaces import IDexterityEditForm
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from redturtle.prenotazioni import _
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import WidgetActionExecutionError
from zope.event import notify
from zope.interface import classImplements
from zope.interface import Invalid
from z3c.form.interfaces import WidgetActionExecutionError
from zope.interface import Invalid
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile as Z3VPTF  # noqa

import re


def negative_delta(data):
    for interval in data['settimana_tipo']:
        if interval['inizio_m'] and not interval['end_m']:
            return True
        if interval['end_m'] and not interval['inizio_m']:
            return True
        if interval['inizio_p'] and not interval['end_p']:
            return True
        if interval['end_p'] and not interval['inizio_p']:
            return True
        if interval['inizio_m'] and interval['end_m']:
            if interval['inizio_m'] > interval['end_m']:
                return True
        if interval['inizio_p'] and interval['end_p']:
            if interval['inizio_p'] > interval['end_p']:
                return True
    return False
    

class DefaultEditForm(BaseEdit):
    """
    """
    def updateWidgets(self):
        super(DefaultEditForm, self).updateWidgets()
        # XXX day name should be only readable
        self.widgets['settimana_tipo'].columns[0]['mode'] = DISPLAY_MODE
        self.widgets['settimana_tipo'].allow_insert = False
        self.widgets['settimana_tipo'].allow_delete = False
        self.widgets['settimana_tipo'].allow_append = False
        self.widgets['settimana_tipo'].allow_reorder = False

    def datagridUpdateWidgets(self, subform, widgets, widget):
        if 'giorno' in widgets.keys():
            widgets['giorno'].template = Z3VPTF('templates/custom_dgf_input.pt')

    @button.buttonAndHandler(_dmf(u'Save'), name='save')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        
        if negative_delta(data):
            raise WidgetActionExecutionError(
                'settimana_tipo',
                Invalid(_(u"Check time intervals."))
            )

        if not data.get('tipologia', []):
            raise WidgetActionExecutionError(
                'tipologia',
                Invalid(_(u"Please add at least one tipology."))
            )

        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(
            _dmf(u"Changes saved"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))

    @button.buttonAndHandler(_dmf(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _dmf(u"Edit cancelled"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditCancelledEvent(self.context))


DefaultEditView = layout.wrap_form(DefaultEditForm)
classImplements(DefaultEditView, IDexterityEditForm)


class DefaultAddForm(BaseAddForm):
    """
    """
    def updateWidgets(self):
        super(DefaultAddForm, self).updateWidgets()
        # XXX day name should be only readable
        self.widgets['settimana_tipo'].columns[0]['mode'] = DISPLAY_MODE
        self.widgets['settimana_tipo'].allow_insert = False
        self.widgets['settimana_tipo'].allow_delete = False
        self.widgets['settimana_tipo'].allow_append = False
        self.widgets['settimana_tipo'].allow_reorder = False

    def datagridUpdateWidgets(self, subform, widgets, widget):
        if 'giorno' in widgets.keys():
            widgets['giorno'].template = Z3VPTF('templates/custom_dgf_input.pt')

    @button.buttonAndHandler(_dmf('Save'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        
        if negative_delta(data):
            raise WidgetActionExecutionError(
                'settimana_tipo',
                Invalid(_(u"Check time intervals."))
            )

        if not data.get('tipologia', []):
            raise WidgetActionExecutionError(
                'tipologia',
                Invalid(_(u"Please add at least one tipology."))
            )

        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            IStatusMessage(self.request).addStatusMessage(
                self.success_message, "info"
            )
            self.request.response.redirect(self.nextURL())

    @button.buttonAndHandler(_dmf(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _dmf(u"Add New Item operation cancelled"), "info"
        )
        self.request.response.redirect(self.nextURL())
        notify(AddCancelledEvent(self.context))


    def nextURL(self):
        return self.context.absolute_url()


class DefaultAddView(BaseAddView):

    form = DefaultAddForm


# -*- coding: utf-8 -*-
from plone.dexterity.browser.add import DefaultAddForm as BaseAddForm
from plone.dexterity.browser.add import DefaultAddView as BaseAddView
from plone.dexterity.browser.edit import DefaultEditForm as BaseEdit
from plone.dexterity.browser.edit import DefaultEditView as BaseEditView

# from Products.CMFPlone.resources import add_bundle_on_request
from zope.interface import implementer
from .viewlets import IHasTableOverridesMarker


class DefaultEditForm(BaseEdit):
    """ """

    def updateWidgets(self):
        super(DefaultEditForm, self).updateWidgets()
        self.widgets["week_table"].allow_insert = False
        self.widgets["week_table"].allow_delete = False
        self.widgets["week_table"].allow_append = False
        self.widgets["week_table"].allow_reorder = False
        self.widgets["week_table"].auto_append = False


@implementer(IHasTableOverridesMarker)
class DefaultEditView(BaseEditView):
    form = DefaultEditForm

    # def __call__(self):
    #     add_bundle_on_request(self.request, "week-table-overrides-widget-bundle")
    #     return super().__call__()


class DefaultAddForm(BaseAddForm):
    """ """

    def updateWidgets(self):
        super(DefaultAddForm, self).updateWidgets()
        self.widgets["week_table"].allow_insert = False
        self.widgets["week_table"].allow_delete = False
        self.widgets["week_table"].allow_append = False
        self.widgets["week_table"].allow_reorder = False
        self.widgets["week_table"].auto_append = False


@implementer(IHasTableOverridesMarker)
class DefaultAddView(BaseAddView):
    form = DefaultAddForm

    # def __call__(self):
    #     add_bundle_on_request(self.request, "week-table-overrides-widget-bundle")
    #     return super().__call__()

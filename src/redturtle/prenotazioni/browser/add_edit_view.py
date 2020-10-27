# -*- coding: utf-8 -*-
from plone.dexterity.browser.add import DefaultAddForm as BaseAddForm
from plone.dexterity.browser.add import DefaultAddView as BaseAddView
from plone.dexterity.browser.edit import DefaultEditForm as BaseEdit
from plone.dexterity.interfaces import IDexterityEditForm
from plone.z3cform import layout
from zope.interface import classImplements


class DefaultEditForm(BaseEdit):
    """
    """

    def updateWidgets(self):
        super(DefaultEditForm, self).updateWidgets()
        self.widgets["week_table"].allow_insert = False
        self.widgets["week_table"].allow_delete = False
        self.widgets["week_table"].allow_append = False
        self.widgets["week_table"].allow_reorder = False
        self.widgets["week_table"].auto_append = False


DefaultEditView = layout.wrap_form(DefaultEditForm)
classImplements(DefaultEditView, IDexterityEditForm)


class DefaultAddForm(BaseAddForm):
    """
    """

    def updateWidgets(self):
        super(DefaultAddForm, self).updateWidgets()
        self.widgets["week_table"].allow_insert = False
        self.widgets["week_table"].allow_delete = False
        self.widgets["week_table"].allow_append = False
        self.widgets["week_table"].allow_reorder = False
        self.widgets["week_table"].auto_append = False


class DefaultAddView(BaseAddView):

    form = DefaultAddForm

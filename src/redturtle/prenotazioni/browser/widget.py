# -*- coding: utf-8 -*-
from z3c.form.browser import widget
from z3c.form.browser.textarea import TextAreaWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import ITextAreaWidget
from z3c.form.widget import FieldWidget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implementer_only
from zope.schema.interfaces import IField


class IWeekTableOverridesWidget(ITextAreaWidget):
    """ """


@implementer_only(IWeekTableOverridesWidget)
class WeekTableOverridesWidget(TextAreaWidget):
    """"""

    klass = "week-table-overrides-widget"
    value = ""
    schema = None

    def update(self):
        super(WeekTableOverridesWidget, self).update()
        widget.addFieldClass(self)

    def json_data(self):
        data = super(WeekTableOverridesWidget, self).json_data()
        data["type"] = "week-table-overrides-widget"
        return data


@adapter(IField, IFormLayer)
@implementer(IFieldWidget)
def WeekTableOverridesFieldWidget(field, request):
    """IFieldWidget factory for TextWidget."""
    return FieldWidget(field, WeekTableOverridesWidget(request))

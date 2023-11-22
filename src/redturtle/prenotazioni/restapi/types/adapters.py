# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.interfaces import IRow
from plone.restapi.types.adapters import ObjectJsonSchemaProvider
from plone.restapi.types.interfaces import IJsonSchemaProvider
from plone.restapi.types.utils import get_fieldsets
from plone.restapi.types.utils import get_jsonschema_properties
from plone.restapi.types.utils import iter_fields
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@adapter(IRow, Interface, Interface)
@implementer(IJsonSchemaProvider)
class DataGridRowJsonSchemaProvider(ObjectJsonSchemaProvider):
    def __init__(self, field, context, request):
        super().__init__(field, context, request)
        self.fieldsets = get_fieldsets(context, request, self.field.schema)

    def get_factory(self):
        return "DataGridField Row"

    def get_properties(self):
        if self.prefix:
            prefix = ".".join([self.prefix, self.field.__name__])
        else:
            prefix = self.field.__name__
        return get_jsonschema_properties(
            self.context, self.request, self.fieldsets, prefix
        )

    def additional(self):
        info = super().additional()
        properties = self.get_properties()
        required = []
        for field in iter_fields(self.fieldsets):
            name = field.field.getName()

            # Determine required fields
            if field.field.required:
                required.append(name)

            # Include field modes
            if field.mode:
                properties[name]["mode"] = field.mode

        info["fieldsets"] = [
            {
                "id": "default",
                "title": "Default",
                "fields": [x for x in properties.keys()],
            },
        ]
        info["required"] = required
        info["properties"] = properties
        return info

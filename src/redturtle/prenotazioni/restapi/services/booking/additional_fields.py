# -*- coding: utf-8 -*-
from plone import api
from redturtle.prenotazioni import _
from zExceptions import BadRequest
from zope.component import getUtility
from zope.schema._bootstrapinterfaces import ValidationError
from zope.schema.interfaces import IVocabularyFactory


def validate_booking_additional_fields(
    context,
    booking_type,
    additional_fields,
    required_value_missing_message=False,
):
    """Validate and normalize booking additional fields."""
    additional_fields = additional_fields or []
    additional_fields_data = []

    field_types_vocabulary = getUtility(
        IVocabularyFactory,
        "redturtle.prenotazioni.booking_additional_fields_types",
    )(context)

    field_types_validators = {
        i.value: i.field_validator for i in field_types_vocabulary
    }

    for field_schema in booking_type.booking_additional_fields_schema or []:
        field = None
        for additional_field in additional_fields:
            if additional_field.get("name") == field_schema.get("name"):
                field = additional_field
                break

        is_required = field_schema.get("required", False)
        value = field and field.get("value")

        if not field and is_required:
            raise BadRequest(
                api.portal.translate(
                    _(
                        "Additional field '${additional_field_name}' is missing.",
                        mapping=dict(additional_field_name=field_schema.get("name")),
                    )
                )
            )
        elif not field:
            continue

        if is_required and not value:
            if required_value_missing_message:
                raise BadRequest(
                    api.portal.translate(
                        _(
                            "Additional field '${additional_field_name}' value is missing.",
                            mapping=dict(
                                additional_field_name=field_schema.get("name")
                            ),
                        )
                    )
                )
            raise BadRequest(
                api.portal.translate(
                    _(
                        "Additional field '${additional_field_name}' is missing.",
                        mapping=dict(additional_field_name=field_schema.get("name")),
                    )
                )
            )

        try:
            field_types_validators.get(field_schema.get("type"))(value)
        except ValidationError as e:
            raise BadRequest(
                api.portal.translate(
                    _(
                        "Could not validate value for the ${field_name} due to: ${err_message}",
                        mapping=dict(
                            field_name=field_schema.get("name"), err_message=str(e)
                        ),
                    )
                )
            )

        additional_fields_data.append({"name": field.get("name"), "value": value})

    return additional_fields_data

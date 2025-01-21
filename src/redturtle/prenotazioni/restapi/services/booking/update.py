# -*- coding: utf-8 -*-
import json

from plone import api
from plone.restapi.deserializer import json_body
from plone.restapi.services.content.update import ContentPatch
from zExceptions import BadRequest
from zope.component import getUtility
from zope.schema._bootstrapinterfaces import ValidationError
from zope.schema.interfaces import IVocabularyFactory

from redturtle.prenotazioni import _


class UpdateBooking(ContentPatch):
    def reply(self, *args, **kwargs):

        self.handle_additional_fields()

        return super().reply(*args, **kwargs)

    def handle_additional_fields(self):
        data = json_body(self.request)
        booking_folder = self.context.getPrenotazioniFolder()

        if data:
            # booking.additional_fields validation below
            additional_fields = data.get("additional_fields") or []

            # rewrite the fields to prevent not required data
            additional_fields_data = []

            field_types_vocabulary = getUtility(
                IVocabularyFactory,
                "redturtle.prenotazioni.booking_additional_fields_types",
            )(booking_folder)

            field_types_validators = {
                i.value: i.field_validator for i in field_types_vocabulary
            }

            booking_type = self.context.get_booking_type()

            # validate additional fields
            # TODO: refactor this code to a separate method to avoid code duplication
            for field_schema in booking_type.booking_additional_fields_schema or []:
                field = None
                for additional_field in additional_fields:
                    if additional_field.get("name") == field_schema.get("name"):
                        field = additional_field
                        break

                if field_schema.get("required", False):
                    if not field or not field.get("value"):
                        raise BadRequest(
                            api.portal.translate(
                                _(
                                    "Additional field '${additional_field_name}' is missing.",
                                    mapping=dict(
                                        additional_field_name=field_schema.get("name")
                                    ),
                                )
                            )
                        )
                elif not field:
                    continue

                try:
                    field_types_validators.get(field_schema.get("type"))(
                        field.get("value")
                    )
                except ValidationError as e:
                    raise BadRequest(
                        api.portal.translate(
                            _(
                                "Could not validate value for the ${field_name} due to: ${err_message}",
                                mapping=dict(
                                    field_name=field_schema.get("name"),
                                    err_message=str(e),
                                ),
                            )
                        )
                    )

                additional_fields_data.append(
                    {"name": field.get("name"), "value": field.get("value")}
                )

            self.request["BODY"] = json.dumps(data).encode()

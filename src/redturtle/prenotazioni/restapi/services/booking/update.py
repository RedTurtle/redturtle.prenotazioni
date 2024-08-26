# -*- coding: utf-8 -*-
import json

from plone import api
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
        data = json.loads(self.request.get("BODY", b"").decode())
        booking_folder = self.context.getPrenotazioniFolder()

        if data:
            # booking.additional_fields validation below
            additional_fields = data.get("additional_fields")

            if additional_fields and type(additional_fields) is list:
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

                for field in additional_fields:
                    field_schema = list(
                        filter(
                            lambda i: i.get("name") == field.get("name"),
                            booking_type.booking_additional_fields_schema,
                        )
                    )

                    if not field_schema:
                        raise BadRequest(
                            api.portal.translate(
                                _(
                                    "Unknown additional field '${additional_field_name}'.",
                                    mapping=dict(
                                        additional_field_name=field.get("name")
                                    ),
                                )
                            )
                        )

                    field_schema = field_schema[0]

                    try:
                        if not field.get("value"):
                            raise BadRequest(
                                api.portal.translate(
                                    _(
                                        "Additional field '${additional_field_name}' value is missing.",
                                        mapping=dict(
                                            additional_field_name=field.get("name")
                                        ),
                                    )
                                )
                            )

                        # Validation
                        field_types_validators.get(field_schema.get("type"))(
                            field.get("value")
                        )

                    except ValidationError as e:
                        raise BadRequest(
                            api.portal.translate(
                                _(
                                    "Could not validate value for the ${field_name} due to: ${err_message}",
                                    mapping=dict(
                                        field_name=field.get("name"), err_message=str(e)
                                    ),
                                )
                            )
                        )

                    additional_fields_data.append(
                        {"name": field.get("name"), "value": field.get("value")}
                    )

                data["additional_fields"] = json.dumps(additional_fields_data)

            self.request["BODY"] = json.dumps(data).encode()

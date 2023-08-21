# -*- coding: utf-8 -*-
from collective.exportimport.export_content import ExportContent
from plone.app.event.base import default_timezone

from datetime import datetime
from copy import deepcopy

import pytz


class CustomExportPrenotazioni(ExportContent):
    """We use this view to convert the datetime values of Prenotazione c.t. to UTC timezone"""

    def dict_hook_prenotazione(self, item, obj):
        item["booking_date"] = self.datetime_iso_to_utc(item["booking_date"])
        item["booking_expiration_date"] = self.datetime_iso_to_utc(
            item["booking_expiration_date"]
        )
        return item

    def dict_hook_prenotazionifolder(self, item, obj):
        for field in item["pause_table"]:
            field["day"] = str(field["day"])

        # delete no more existent values from the `visible_booking_fields`
        for field_to_delete in ("description",):
            for field in deepcopy(item["visible_booking_fields"]):
                if field == field_to_delete:
                    item["visible_booking_fields"].remove(field_to_delete)

        # delete no more existent values from the `required_booking_fields`
        for field_to_delete in ("booking_type",):
            for field in deepcopy(item["required_booking_fields"]):
                if field == field_to_delete:
                    item["required_booking_fields"].remove(field_to_delete)

        # case we have the 'today' date setted
        if item["same_day_booking_disallowed"] not in ("yes", "no"):
            item["same_day_booking_disallowed"] = "no"

        return item

    def datetime_iso_to_utc(self, dt: str) -> str:
        return (
            pytz.timezone(default_timezone())
            .localize(datetime.fromisoformat(dt))
            .astimezone(pytz.timezone("UTC"))
        ).isoformat()

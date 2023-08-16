from collective.exportimport.export_content import ExportContent
from plone.app.event.base import default_timezone
from datetime import datetime

import pytz


class CustomExportPrenotazioni(ExportContent):
    """We use this view to convert the datetime values of Prenotazione c.t. to UTC timezone"""

    def dict_hook_prenotazione(self, item, obj):
        item["booking_date"] = self.datetime_iso_to_utc(item["booking_date"])
        item["booking_expiration_date"] = self.datetime_iso_to_utc(
            item["booking_expiration_date"]
        )
        return item

    def datetime_iso_to_utc(self, dt: str) -> str:
        return (
            pytz.timezone(default_timezone())
            .localize(datetime.fromisoformat(dt))
            .astimezone(pytz.timezone("UTC"))
        ).isoformat()

# -*- coding: utf-8 -*-
import calendar
import json
from datetime import date

from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import Invalid
from zope.schema import ValidationError

from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.slot import interval_is_contained
from redturtle.prenotazioni.adapters.slot import is_intervals_overlapping


def get_dgf_values_from_request(request, fieldname, columns=[]):
    """
    Validator with datagridfield works in a fuzzy way. We need to extract
    values from request to be sure we are validating correct data.
    """

    def get_from_form(form, fieldname):
        value = form.get(fieldname, None)
        if value:
            if isinstance(value, list):
                return value[0]
            if isinstance(value, str):
                return value
        return None

    number_of_entry = request.form.get("form.widgets.{}.count".format(fieldname))
    data = []
    prefix = "form.widgets.{}".format(fieldname)
    for counter in range(int(number_of_entry)):
        row_data = {}
        for column in columns:
            indexed_prefix = "{}.{}.widgets.".format(prefix, counter)
            row_data.update(
                {
                    column: get_from_form(
                        request.form, "{}{}".format(indexed_prefix, column)
                    )
                }
            )
        data.append(row_data)
    return data


def validate_pause_table(data={}):
    """Pause validator"""
    pause_table = getattr(data, "pause_table", [])
    week_table = getattr(data, "week_table", [])

    if not (pause_table and week_table):
        return

    # validate pauses
    groups_of_pause = {}
    for pause in pause_table:
        groups_of_pause.setdefault(pause["day"], []).append(pause)

    for day in groups_of_pause:
        day_hours = week_table[int(day)]
        for pause in groups_of_pause[day]:
            #  0. Of course if we don't have a correct interval we can't do
            # more steps
            if pause["pause_end"] is None or pause["pause_start"] is None:
                raise Invalid(
                    translate(
                        _("You must set both start and end"), context=getRequest()
                    )
                )

            # 1. Pause starts should always be bigger than pause ends
            if not (pause["pause_end"] > pause["pause_start"]):
                raise Invalid(
                    translate(
                        _("Pause end should be greater than pause start"),
                        context=getRequest(),
                    )
                )
            interval = [pause["pause_start"], pause["pause_end"]]

            # 2. two pause interval on the same day should not overlap
            if is_intervals_overlapping(
                [
                    (pause["pause_start"], pause["pause_end"])
                    for pause in groups_of_pause[day]
                ]
            ):
                raise Invalid(
                    translate(
                        _("In the same day there are overlapping intervals"),
                        context=getRequest(),
                    )
                )

            # 3. a pause interval should always be contained in the morning
            # or afternoon defined for these days

            morning_includes_interval = False
            afternoon_includes_interval = False
            if day_hours["morning_start"] and day_hours["morning_end"]:
                if interval_is_contained(
                    interval,
                    day_hours["morning_start"],
                    day_hours["morning_end"],
                ):
                    morning_includes_interval = True

            if day_hours["afternoon_start"] and day_hours["afternoon_end"]:
                if interval_is_contained(
                    interval,
                    day_hours["afternoon_start"],
                    day_hours["afternoon_end"],
                ):
                    afternoon_includes_interval = True

            if not (morning_includes_interval or afternoon_includes_interval):
                raise Invalid(
                    translate(
                        _(
                            "Pause should be included in morning slot or afternoon slot"  # noqa
                        ),
                        context=getRequest(),
                    )
                )


class CustomValidationError(ValidationError):
    def doc(self):
        if len(self.args) == 1:
            return translate(self.args[0], context=getRequest())
        return super().doc()


def checkOverrides(value):
    overrides = json.loads(value)
    now = date.today()
    for override in overrides:
        from_month = override.get("from_month", "")
        from_day = override.get("from_day", "")
        to_month = override.get("to_month", "")
        to_day = override.get("to_day", "")
        # check from
        if not from_month and not from_day:
            raise CustomValidationError(
                _("from_month_error", default="You should set a start range.")
            )
        from_month = int(from_month)
        from_day = int(from_day)
        from_month_days = calendar.monthrange(now.year, from_month)[1]
        if from_day > from_month_days:
            raise CustomValidationError(
                _(
                    "from_month_too_days_error",
                    default='Selected day is too big for that month for "from" field.',
                )
            )
        # check to
        if not to_month and not to_day:
            raise CustomValidationError(
                _("to_month_error", default="You should set an end range.")
            )
        to_month = int(to_month)
        to_day = int(to_day)
        to_month_days = calendar.monthrange(now.year, to_month)[1]
        if to_day > to_month_days:
            raise CustomValidationError(
                _(
                    "to_month_too_days_error",
                    default='Selected day is too big for that month for "to" field.',
                )
            )

        for interval in override["week_table"]:
            if interval["morning_start"] and not interval["morning_end"]:
                raise CustomValidationError(
                    _("You should set an end time for morning.")
                )
            if interval["morning_end"] and not interval["morning_start"]:
                raise CustomValidationError(
                    _("You should set a start time for morning.")
                )
            if interval["afternoon_start"] and not interval["afternoon_end"]:
                raise CustomValidationError(
                    _("You should set an end time for afternoon.")
                )
            if interval["afternoon_end"] and not interval["afternoon_start"]:
                raise CustomValidationError(
                    _("You should set a start time for afternoon.")
                )
            if interval["morning_start"] and interval["morning_end"]:
                if interval["morning_start"] > interval["morning_end"]:
                    raise CustomValidationError(
                        _("Morning start should not be greater than end.")
                    )
            if interval["afternoon_start"] and interval["afternoon_end"]:
                if interval["afternoon_start"] > interval["afternoon_end"]:
                    raise CustomValidationError(
                        _("Afternoon start should not be greater than end.")
                    )

    return True

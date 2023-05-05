# -*- coding: utf-8 -*-
from datetime import date
from zope.schema import ValidationError
from redturtle.prenotazioni import _
from zope.interface import Invalid
from z3c.form import validator
from redturtle.prenotazioni.adapters.slot import interval_is_contained
from redturtle.prenotazioni.adapters.slot import is_intervals_overlapping


import calendar
import json


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


class PauseValidator(validator.SimpleFieldValidator):
    """z3c.form validator class for international phone numbers"""

    def validate(self, pause_table):
        """Validate international phone number on input"""
        super(PauseValidator, self).validate(pause_table)
        pause_table = get_dgf_values_from_request(
            self.context.REQUEST,
            "pause_table",
            ["day", "pause_start", "pause_end"],
        )
        if not pause_table:
            return

        week_table = get_dgf_values_from_request(
            self.context.REQUEST,
            "week_table",
            [
                "day",
                "morning_start",
                "morning_end",
                "afternoon_start",
                "afternoon_end",
            ],
        )

        # validate pauses
        groups_of_pause = {}
        for pause in pause_table:
            groups_of_pause.setdefault(pause["day"], []).append(pause)

        for day in groups_of_pause:
            day_hours = week_table[int(day)]
            for pause in groups_of_pause[day]:
                #  0. Of course if we don't have a correct interval we can't do
                # more steps
                if (
                    pause["pause_end"] == "--NOVALUE--"
                    or pause["pause_start"] == "--NOVALUE--"
                ):
                    raise Invalid(_("You must set both start and end"))

                # 1. Pause starts should always be bigger than pause ends
                if not (pause["pause_end"] > pause["pause_start"]):
                    raise Invalid(_("Pause end should be greater than pause start"))
                interval = [pause["pause_start"], pause["pause_end"]]
                # 2. a pause interval should always be contained in the morning
                # or afternoon defined for these days
                if not (
                    interval_is_contained(
                        interval,
                        day_hours["morning_start"],
                        day_hours["morning_end"],
                    )
                    or interval_is_contained(
                        interval,
                        day_hours["afternoon_start"],
                        day_hours["afternoon_end"],
                    )
                ):
                    raise Invalid(
                        _(
                            "Pause should be included in morning slot or afternoon slot"  # noqa
                        )
                    )
            # 3. two pause interval on the same day should not overlap
            if is_intervals_overlapping(
                [
                    (pause["pause_start"], pause["pause_end"])
                    for pause in groups_of_pause[day]
                ]
            ):
                raise Invalid(
                    _("In the same day there are overlapping intervals")
                )  # noqa


class CustomValidationError(ValidationError):
    def doc(self):
        if len(self.args) == 1:
            return self.args[0]
        return super().doc()


def checkOverrides(value):
    overrides = json.loads(value)
    now = date.today()
    for override in overrides:

        fromMonth = override.get("fromMonth", "")
        fromDay = override.get("fromDay", "")
        toMonth = override.get("toMonth", "")
        toDay = override.get("toDay", "")
        # check from
        if not fromMonth and not fromDay:
            raise CustomValidationError(
                _("from_month_error", default="You should set a start range.")
            )
        fromMonth = int(fromMonth)
        fromDay = int(fromDay)
        from_month_days = calendar.monthrange(now.year, fromMonth)[1]
        if fromDay > from_month_days:
            raise CustomValidationError(
                _(
                    "from_month_too_days_error",
                    default='Selected day is too big for that month for "from" field.',
                )
            )
        # check to
        if not toMonth and not toDay:
            raise CustomValidationError(
                _("to_month_error", default="You should set a start range.")
            )
        toMonth = int(toMonth)
        toDay = int(toDay)
        to_month_days = calendar.monthrange(now.year, toMonth)[1]
        if toDay > to_month_days:
            raise CustomValidationError(
                _(
                    "to_month_too_days_error",
                    default='Selected day is too big for that month for "to" field.',
                )
            )

        for interval in override["week_table"]:
            if interval["morning_start"] and not interval["morning_end"]:
                raise CustomValidationError(
                    _("You should set and end time for morning.")
                )
            if interval["morning_end"] and not interval["morning_start"]:
                raise CustomValidationError(
                    _("You should set a start time for morning.")
                )
            if interval["afternoon_start"] and not interval["afternoon_end"]:
                raise CustomValidationError(
                    _("You should set and end time for afternoon.")
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

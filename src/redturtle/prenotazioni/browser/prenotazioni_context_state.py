# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import date
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from plone import api
from plone.memoize.view import memoize
from Products.Five.browser import BrowserView
from redturtle.prenotazioni import _
from redturtle.prenotazioni import get_or_create_obj
from redturtle.prenotazioni import logger
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.adapters.conflict import IConflictManager
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.adapters.slot import ISlot
from redturtle.prenotazioni.config import PAUSE_PORTAL_TYPE
from redturtle.prenotazioni.config import PAUSE_SLOT
from redturtle.prenotazioni.content.pause import Pause
from redturtle.prenotazioni.content.prenotazione_type import PrenotazioneType
from redturtle.prenotazioni.utilities.dateutils import hm2DT
from redturtle.prenotazioni.utilities.dateutils import hm2seconds
from redturtle.prenotazioni.utilities.urls import urlify
from six.moves import map
from six.moves import range

import itertools
import json
import six


class PrenotazioniContextState(BrowserView):
    """
    This is a view to for checking prenotazioni context state
    """

    active_review_state = ["confirmed", "pending"]
    add_view = "prenotazione_add"
    day_type = "PrenotazioniDay"
    week_type = "PrenotazioniWeek"
    year_type = "PrenotazioniYear"

    busy_slot_booking_url = {"url": "", "title": _("busy", "Busy")}
    unavailable_slot_booking_url = {"url": "", "title": ""}

    @property
    @memoize
    def is_anonymous(self):
        """
        Return the conflict manager for this context
        """
        return api.user.is_anonymous()

    @property
    @memoize
    def user_roles(self):
        """The dict with the user permissions"""
        return api.user.get_roles(obj=self.context)

    @property
    @memoize
    def user_can_manage(self):
        """States if the authenticated user can manage this context"""
        if self.is_anonymous:
            return False
        return api.user.has_permission("Modify portal content", obj=self.context)

    @property
    @memoize
    def user_can_view(self):
        """States if the authenticated user can manage this context"""
        if self.is_anonymous:
            return False
        if self.user_can_manage:
            return True
        # if u"Reader" in self.user_roles:
        #     return True
        return False

    @property
    @memoize
    def user_can_search(self):
        """States if the user can see the search button"""
        return self.user_can_manage

    @property
    @memoize
    def user_can_manage_prenotazioni(self):
        """States if the authenticated user can manage prenotazioni in this context"""
        return api.user.has_permission(
            "redturtle.prenotazioni: Manage Prenotazioni", obj=self.context
        )

    @property
    @memoize
    def bookins_manager_is_restricted_by_dates(self):
        """Bookings manager is restricted by dates as an usual user"""
        return self.context.apply_date_restrictions_to_manager

    @property
    @memoize
    def booker(self):
        """
        Return the conflict manager for this context
        """
        return IBooker(self.context.aq_inner)

    @property
    @memoize
    def today(self):
        """Cache for today date"""
        return date.today()

    @property
    @memoize
    def yesterday(self):
        """Cache for today date"""
        return self.today - timedelta(days=1)

    @property
    @memoize
    def tomorrow(self):
        """Cache for today date"""
        return self.today + timedelta(days=1)

    @property
    @memoize
    def same_day_booking_allowed(self):
        """State if the same day booking is allowed"""
        value = getattr(self.context, "same_day_booking_disallowed")
        return value == "no"

    @property
    @memoize
    def first_bookable_day(self):
        """The first day when you can book stuff

        ;return; a datetime.date object
        """
        if self.same_day_booking_allowed:
            return max(self.context.getDaData(), self.today)
        return max(self.context.getDaData(), self.tomorrow)

    @property
    @memoize
    def last_bookable_day(self):
        """The last day (if set) when you can book stuff

        ;return; a datetime.date object or None
        """
        adata = self.context.getAData()
        if not adata:
            return
        return adata

    @property
    @memoize
    def future_days_limit(self):
        return self.context.getFutureDays()

    @memoize
    def is_vacation_day(self, date):
        """
        Check if today is a vacation day
        """
        year = repr(date.year)
        date_it = date.strftime("%d/%m/%Y")
        holidays = getattr(self.context, "holidays", [])
        if not holidays:
            return False
        for holiday in holidays:
            if date_it in holiday.replace("*", year):
                return True
        return False

    @memoize
    def is_configured_day(self, day):
        """Returns True if the day has been configured"""
        weekday = day.weekday()
        week_table = self.get_week_table(day=day)
        for gate_schedule in week_table.values():
            day_table = gate_schedule[weekday]
            if any(
                (
                    day_table["morning_start"],
                    day_table["morning_end"],
                    day_table["afternoon_start"],
                    day_table["afternoon_end"],
                )
            ):
                return True
        return False

    def get_week_overrides(self, day):
        week_table_overrides = json.loads(
            getattr(self.context, "week_table_overrides", "[]") or "[]"
        )

        if not week_table_overrides:
            return []

        overrides = []
        unlimited_overrides = []

        for override in week_table_overrides:
            from_year = int(override.get("from_year", 0))
            from_month = int(override.get("from_month", ""))
            from_day = int(override.get("from_day", ""))

            to_year = int(override.get("to_year", 0))
            to_month = int(override.get("to_month", ""))
            to_day = int(override.get("to_day", ""))

            booking_date = day

            if from_year and to_year:
                from_date = date(from_year, from_month, from_day)
                to_date = date(to_year, to_month, to_day)

                if isinstance(day, datetime):
                    booking_date = day.date()

                if from_date <= booking_date <= to_date:
                    overrides.append(override)

            else:
                to_year = day.year

                if from_month <= to_month:
                    # same year (i.e from "10 aug" to "4 sep")
                    from_date = date(to_year, from_month, from_day)
                    to_date = date(to_year, to_month, to_day)

                else:
                    # ends next year (i.e. from "20 dec" to "7 jan")
                    if day.month < from_month:
                        # i.e day is 03 jan
                        from_date = date(to_year - 1, from_month, from_day)
                        to_date = date(to_year, to_month, to_day)

                    else:
                        # i.e day is 28 dec
                        from_date = date(to_year, from_month, from_day)
                        to_date = date(to_year + 1, to_month, to_day)

                if isinstance(day, datetime):
                    booking_date = day.date()

                if from_date <= booking_date <= to_date:
                    unlimited_overrides.append(override)

        # More specific overrides first
        overrides = unlimited_overrides + overrides

        # remove double gates, we are interested only about the last one
        gates = []

        for i, j in reversed(list(enumerate(overrides))):
            for gate in deepcopy(j.get("gates", [])):
                if gate in gates:
                    overrides[i]["gates"].remove(gate)
                else:
                    gates.append(gate)

        return overrides

    def get_week_table(self, day):
        """
        return week table divided by gates because overrides can have
        different gate timetables
        """
        overrides = self.get_week_overrides(day)
        week_table = getattr(self.context, "week_table", [])
        gates = getattr(self.context, "gates", [])
        if not overrides:
            return {k: week_table for k in gates}
        res = {}
        for override in overrides:
            override_gates = override.get("gates", []) or gates
            override_week_table = override.get("week_table", []) or week_table
            for gate in override_gates:
                res[gate] = override_week_table
        return res

    def is_before_allowed_period(self, day, bypass_user_restrictions=False):
        """Returns True if the day is before the first bookable day"""
        date_limit = not bypass_user_restrictions and self.minimum_bookable_date or None

        if not date_limit:
            return False
        if day <= date_limit.date():
            return True
        return False

    @memoize
    def is_valid_day(self, day, bypass_user_restrictions=False):
        """Returns True if the day is valid
        Day is not valid in those conditions:
            - day is out of validity range
                (not applied to BookingManager if PrenotazioniFolder.bookins_manager_is_restricted_by_dates is False)
            - day is vacation day
            - day is out of PrenotazioniFolder.futures_day range
                (not applied to BookingManager if PrenotazioniFolder.bookins_manager_is_restricted_by_dates is False)
            - week day is not configured
        """

        if isinstance(day, datetime):
            day = day.date()

        is_configured_day = self.is_configured_day(day)

        if self.is_vacation_day(day):
            return False

        if bypass_user_restrictions:
            return True

        if (
            is_configured_day
            and self.user_can_manage_prenotazioni
            and not self.bookins_manager_is_restricted_by_dates
        ):
            return True

        if day < self.first_bookable_day:
            return False

        if self.last_bookable_day and day > self.last_bookable_day:
            return False

        if self.is_before_allowed_period(day, bypass_user_restrictions=False):
            return False

        if self.future_days_limit:
            date_limit = date.today() + timedelta(days=self.future_days_limit)

            if day >= date_limit:
                return False

        return is_configured_day

    @property
    @memoize
    def conflict_manager(self):
        """
        Return the conflict manager for this context
        """
        return IConflictManager(self.context.aq_inner)

    @memoize
    def get_state(self, context):
        """Facade to the api get_state method"""
        if not context:
            return
        if context.portal_type == PAUSE_PORTAL_TYPE:
            return PAUSE_SLOT
        return api.content.get_state(context)

    @property
    @memoize
    def remembered_params(self):
        """We want to remember some parameters"""
        params = dict(
            (key, value)
            for key, value in six.iteritems(self.request.form)
            if (
                value
                and key.startswith("form.")
                and not key.startswith("form.action")
                and key not in ("form.booking_date",)
                or key in ("disable_plone.leftcolumn", "disable_plone.rightcolumn")
            )
        )
        for key, value in six.iteritems(params):
            if isinstance(value, six.text_type):
                params[key] = value
        return params

    @property
    @memoize
    def base_booking_url(self):
        """Return the base booking url (no parameters) for this context"""
        return "%s/%s" % (self.context.absolute_url(), self.add_view)

    def get_booking_urls(
        self, day, slot, slot_min_size=0, gate=None, bypass_user_restrictions=False
    ):
        """Returns, if possible, the booking urls

        slot_min_size: seconds
        """
        # we have some conditions to check
        if not self.is_valid_day(
            day, bypass_user_restrictions=bypass_user_restrictions
        ):
            return []
        if self.maximum_bookable_date and day > self.maximum_bookable_date.date():
            return []
        # date = day.strftime("%Y-%m-%d")
        params = self.remembered_params.copy()
        times = slot.get_values_hr_every(300, slot_min_size=slot_min_size)
        base_url = self.base_booking_url
        urls = []
        now = tznow()
        # times are in localtime
        for t in times:
            booking_date = hm2DT(day, t)
            params["form.booking_date"] = booking_date.isoformat()
            if gate:
                params["gate"] = gate
            urls.append(
                {
                    "title": t,
                    "url": urlify(base_url, params=params),
                    "class": t.endswith(":00") and "oclock" or None,
                    "booking_date": booking_date,
                    "future": now <= booking_date,
                }
            )
        return urls

    def get_all_booking_urls_by_gate(
        self, day, slot_min_size=0, bypass_user_restrictions=False
    ):
        """Get all the booking urls divided by gate

        XXX: used only by 'get_all_booking_urls' !!!

        slot_min_size: seconds

        Return a dict like {
            gate: [
                {
                    'title': '08:00',
                    'url': 'http://.../prenotazione_add?form.booking_date=2023-08-09T08%3A00%3A00%2B02%3A00',
                    'class': 'oclock',
                    'booking_date': datetime.datetime(2023, 8, 9, 8, 0, tzinfo=<DstTzInfo 'Europe/Rome' CEST+2:00:00 DST>),
                    'future': False
                 },
                {
                    'title': '08:05',
                 ...
                ]
            }
        """
        urls = {}
        if not self.is_valid_day(
            day, bypass_user_restrictions=bypass_user_restrictions
        ):
            return urls
        if self.maximum_bookable_date and day > self.maximum_bookable_date.date():
            return urls
        slots_by_gate = self.get_free_slots(day)
        for gate in slots_by_gate:
            slots = slots_by_gate[gate]
            for slot in slots:
                slot_urls = self.get_booking_urls(
                    day,
                    slot,
                    slot_min_size=slot_min_size,
                    bypass_user_restrictions=bypass_user_restrictions,
                )
                urls.setdefault(gate, []).extend(slot_urls)
        return urls

    def get_all_booking_urls(
        self, day, slot_min_size=0, bypass_user_restrictions=False
    ):
        """Get all the booking urls

        Not divided by gate

        slot_min_size: seconds
        """
        urls_by_gate = self.get_all_booking_urls_by_gate(
            day, slot_min_size, bypass_user_restrictions=bypass_user_restrictions
        )
        urls = {}
        for url in itertools.chain.from_iterable(urls_by_gate.values()):
            urls[url["title"]] = url
        return sorted(urls.values(), key=lambda x: x["title"])

    def is_slot_busy(self, day, slot):
        """Check if a slot is busy (i.e. the is no free slot overlapping it)"""
        free_slots = self.get_free_slots(day)
        for gate in free_slots:
            for free_slot in free_slots[gate]:
                intersection = slot.intersect(free_slot)
                if intersection:
                    if intersection.lower_value != intersection.upper_value:
                        return False
        return True

    @memoize
    def get_anonymous_booking_url(
        self, day, slot, slot_min_size=0, bypass_user_restrictions=False
    ):
        """Returns, the the booking url for an anonymous user

        Returns the first available/bookable slot/url that fits
        the slot boundaries

        slot_min_size: seconds
        """
        # First we check if we have booking urls
        all_booking_urls = self.get_all_booking_urls(
            day, slot_min_size, bypass_user_restrictions=bypass_user_restrictions
        )
        if not all_booking_urls:
            # If not the slot can be unavailable or busy
            if self.is_slot_busy(day, slot):
                return self.busy_slot_booking_url
            else:
                return self.unavailable_slot_booking_url
        # Otherwise we check if the URL fits the slot boundaries
        # HH:MM in localtime
        slot_start = slot.start()
        slot_stop = slot.stop()

        for booking_url in all_booking_urls:
            if slot_start <= booking_url["title"] < slot_stop:
                if self.is_booking_date_bookable(booking_url["booking_date"]):
                    return booking_url
        return self.unavailable_slot_booking_url

    @memoize
    def get_gates(self, booking_date=None):
        """
        Get the gates for booking_date
        """

        if isinstance(booking_date, datetime):
            # sometimes booking_date is passed as date and sometimes as datetime
            booking_date = booking_date.date()

        gates = [
            {
                "name": gate,
                "available": True,
            }
            for gate in self.context.getGates() or [""]
        ]

        overrides = self.get_week_overrides(day=booking_date)
        if not overrides:
            return gates

        overrided_gates = []
        for override in overrides:
            overrided_gates.extend(override.get("gates", []))
        if not overrided_gates:
            return gates

        overrided_gates = [
            {
                "name": gate,
                "available": True,
            }
            for gate in overrided_gates or [""]
        ]

        # set default gates as unavailable
        gates = [
            {
                "name": gate["name"],
                "available": False,
            }
            for gate in gates
            if gate["name"] not in [i["name"] for i in overrided_gates]
        ]

        return gates + overrided_gates

    def get_busy_gates_in_slot(self, booking_date, booking_end_date=None):
        """
        The gates already associated to a Prenotazione object for booking_date

        :param booking_date: a DateTime object
        """
        active_review_states = ["confirmed", "pending"]
        brains = self.conflict_manager.unrestricted_prenotazioni(
            Date={
                "query": [
                    DateTime(booking_date.date().__str__()),
                    DateTime(booking_date.date().__str__()) + 1,
                ],
                "range": "minmax",
            },
            review_state=active_review_states,
        )
        gates = self.get_full_gates_in_date(
            prenotazioni=brains,
            booking_date=booking_date,
            booking_end_date=booking_end_date,
        )
        return gates

    def get_full_gates_in_date(
        self, prenotazioni, booking_date, booking_end_date=None
    ):  # noqa
        gates = set()
        for brain in prenotazioni:
            prenotazione = brain._unrestrictedGetObject()
            start = prenotazione.getBooking_date()
            end = prenotazione.getBooking_expiration_date()
            gate = getattr(prenotazione, "gate", "")
            if booking_date < start:
                # new booking starts before current booking
                if booking_end_date > start:
                    # new booking intersect current booking
                    gates.add(gate)
            elif booking_date == start:
                # starts at the same time, so disable curretn booking gate
                gates.add(gate)
            else:
                if booking_date < end:
                    # new booking starts inside current booking interval
                    gates.add(gate)
        return gates

    def get_free_gates_in_slot(self, booking_date, booking_end_date=None):
        """
        The gates not associated to a Prenotazione object for booking_date

        :param booking_date: a DateTime object
        """
        date_slot = BaseSlot(start=booking_date, stop=booking_end_date)
        available = set()
        for gate, slots in self.get_free_slots(booking_date).items():
            for slot in slots:
                if date_slot in slot:
                    available.add(gate)
                    break
        busy = set(self.get_busy_gates_in_slot(booking_date, booking_end_date))
        return available - busy

    @memoize
    def get_day_intervals(self, day):
        """
        Return the time ranges of this day

        Example of returned data:

        {
            'afternoon': {
                'gates': {
                    'uno': [:],
                    'due': [:],
                    'tre': [:],
                },
                'start': '',
                'stop': ''
            },
            'break': {
                'gates': {
                    'uno': [13:00:13:00],
                    'due': [13:00:13:00],
                    'tre': [:]},
                'start': '13:00',
                'stop': '13:00'
            },
            'day': {
                'gates': {
                    'uno': [07:00:13:00],
                    'due': [07:00:13:00],
                    'tre': [:],
                },
                'start': '07:00',
                'stop': '13:00'
            },
            'morning': {
                'gates': {
                    'uno': [07:00:13:00],
                    'due': [07:00:13:00],
                    'tre': [:],
                },
                'start': '07:00',
                'stop': '13:00'
            },
            'stormynight': {
                'gates': {
                    'uno': [:24:00],
                    'due': [:24:00],
                    'tre': [:24:00],
                },
                'start': '',
                'stop': '24:00',
            }}
        """

        weekday = day.weekday()
        res = {
            "morning": {"gates": {}},
            "break": {"gates": {}},
            "afternoon": {"gates": {}},
            "day": {"gates": {}},
            "stormynight": {"gates": {}},
        }
        for gate, week_table in self.get_week_table(day=day).items():
            try:
                day_table = week_table[weekday]
            except IndexError as e:
                logger.warning(e)
                continue
            morning_start = hm2DT(day, day_table["morning_start"])
            morning_end = hm2DT(day, day_table["morning_end"])
            afternoon_start = hm2DT(day, day_table["afternoon_start"])
            afternoon_end = hm2DT(day, day_table["afternoon_end"])

            for slot in ["morning", "afternoon", "day", "break"]:
                if slot == "day":
                    start = morning_start or afternoon_start
                    end = afternoon_end or morning_end
                elif slot == "break":
                    start = morning_end or afternoon_end
                    end = afternoon_start or morning_end
                else:
                    start = hm2DT(day, day_table[f"{slot}_start"])
                    end = hm2DT(day, day_table[f"{slot}_end"])
                res[slot]["gates"][gate] = BaseSlot(
                    start=start, stop=end, gate="", date=day
                )

            res["stormynight"]["gates"][gate] = BaseSlot(
                start=0, stop=86400, gate="", date=day
            )
        # calculate start and end for each slot
        for slot in ["morning", "afternoon", "day", "break"]:
            start = [x.start() for x in res[slot]["gates"].values() if x.start()]
            stop = [x.stop() for x in res[slot]["gates"].values() if x.stop()]
            start = start and min(start) or ""
            stop = stop and max(stop) or ""
            res[slot]["interval"] = BaseSlot(
                start=hm2DT(day, start), stop=hm2DT(day, stop), gate="", date=day
            )
        res["stormynight"]["interval"] = BaseSlot(
            start=0, stop=86400, gate="", date=day
        )
        return res

    @property
    @memoize
    def weektable_boundaries(self):
        """Return the boundaries to draw the week table

        return a dict_like {'morning': slot1,
                            'afternoon': slot2}
        """
        week_table = getattr(self.context, "week_table", {})
        boundaries = {}
        for key in ("morning_start", "afternoon_start"):
            boundaries[key] = min(
                day_table[key] for day_table in week_table if day_table[key]
            )
        for key in ("morning_end", "afternoon_end"):
            boundaries[key] = max(
                day_table[key] for day_table in week_table if day_table[key]
            )
        for key, value in six.iteritems(boundaries):
            boundaries[key] = hm2seconds(value)
        return {
            "morning": BaseSlot(boundaries["morning_start"], boundaries["morning_end"]),
            "afternoon": BaseSlot(
                boundaries["afternoon_start"], boundaries["afternoon_end"]
            ),
        }

    @property
    @memoize
    def maximum_bookable_date(self):
        """Return the maximum bookable date

        return a datetime or None
        """
        if self.user_can_manage_prenotazioni:
            # Gestori prenotazioni can book always
            return
        future_days = self.context.getFutureDays()
        if not future_days:
            return
        date_limit = tznow() + timedelta(future_days)
        return date_limit

    @property
    @memoize
    def minimum_bookable_date(self):
        """Return the minimum bookable date

        return a datetime or None
        """
        notbefore_days = self.context.getNotBeforeDays()
        if not notbefore_days:
            return
        date_limit = tznow() + timedelta(notbefore_days)
        return date_limit

    def get_container(self, booking_date, create_missing=False):
        """Return the container for bookings in this date

        :param booking_date: a date as a string, DateTime or datetime
        :param create_missing: if set to True and the container is missing,
                               create it
        """
        if isinstance(booking_date, six.string_types):
            booking_date = DateTime(booking_date)
        if not create_missing:
            relative_path = booking_date.strftime("%Y/%W/%u")
            return self.context.unrestrictedTraverse(relative_path, None)
        year_id = booking_date.strftime("%Y")
        year = get_or_create_obj(self.context, year_id, self.year_type)
        week_id = booking_date.strftime("%W")
        week = get_or_create_obj(year, week_id, self.week_type)
        day_id = booking_date.strftime("%u")
        day = get_or_create_obj(week, day_id, self.day_type)
        return day

    @memoize
    def get_bookings_in_day_folder(self, booking_date):
        """
        The Prenotazione objects for today, unfiltered but sorted by dates

        :param booking_date: a date as a datetime or a string
        """
        day_folder = self.get_container(booking_date)
        if not day_folder:
            return []
        allowed_portal_type = self.booker.portal_type
        bookings = [
            item[1]
            for item in day_folder.items()
            if item[1].portal_type == allowed_portal_type
        ]
        bookings.sort(
            key=lambda x: (x.getBooking_date(), x.getBooking_expiration_date())
        )
        return bookings

    def get_pauses_in_day_folder(self, booking_date):
        """
        This method takes all pauses from the week table and convert it on slot
        :param booking_date: a date as a datetime or a string
        """
        pause_table = self.context.pause_table or []
        overrides = self.get_week_overrides(day=booking_date)
        if overrides:
            override_value = []
            for override in overrides:
                override_pause_table = override.get("pause_table", [])
                override_value.extend(override_pause_table)
            if override_value:
                pause_table = override_value
        if not pause_table:
            return []

        weekday = booking_date.weekday()

        today_pauses = [row for row in pause_table if row["day"] == str(weekday)]
        pauses = []
        for pause in today_pauses:
            pause = Pause(
                start=pause["pause_start"][:2] + ":" + pause["pause_start"][2:],
                stop=pause["pause_end"][:2] + ":" + pause["pause_end"][2:],
                date=booking_date,
            )
            pauses.append(pause)
        return pauses

    @memoize
    def get_existing_slots_in_day_folder(self, booking_date):
        """
        The Prenotazione objects and eventually the pauses for today

        :param booking_date: a date as a datetime or a string
        """
        bookings = self.get_bookings_in_day_folder(booking_date)
        pauses = self.get_pauses_in_day_folder(booking_date)
        bookings_list = list(map(ISlot, bookings))
        pauses_list = list(map(ISlot, pauses))
        return bookings_list + pauses_list

    def get_busy_slots_in_stormynight(self, booking_date):
        """This will show the slots that will not show elsewhere"""
        morning_slots = self.get_busy_slots_in_period(booking_date, "morning")
        afternoon_slots = self.get_busy_slots_in_period(booking_date, "afternoon")
        all_slots = self.get_existing_slots_in_day_folder(booking_date)
        return sorted(
            [
                slot
                for slot in all_slots
                if not (slot in morning_slots or slot in afternoon_slots)
            ]
        )

    @memoize
    def get_busy_slots_in_period(self, booking_date, period="day"):
        """
        The busy slots objects for today: this filters the slots by review
        state

        :param booking_date: a datetime object
        :param period: a string
        :return: al list of slots
        [slot1, slot2, slot3]
        """
        if period == "stormynight":
            return self.get_busy_slots_in_stormynight(booking_date)
        intervals = self.get_day_intervals(booking_date)
        if not intervals:
            return []
        interval = intervals[period]["interval"]
        if interval.start() == "" and interval.stop() == "":
            return []
        allowed_review_states = ["pending", "confirmed", PAUSE_SLOT]

        slots = self.get_existing_slots_in_day_folder(booking_date)
        # the ones in the interval
        slots = [slot for slot in slots if slot.overlaps(interval)]
        # the one with the allowed review_state
        slots = [
            slot
            for slot in slots
            if self.get_state(slot.context) in allowed_review_states
        ]
        return sorted(slots)

    @memoize
    def get_busy_slots(self, booking_date, period="day"):
        """This will return the busy slots divided by gate:

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'gate1': [slot1],
         'gate2': [slot2, slot3],
        }
        """
        slots_by_gate = {}
        busy_slots = self.get_busy_slots_in_period(booking_date, period)
        day_intervals = self.get_day_intervals(booking_date)
        for slot in busy_slots:
            if slot.context.portal_type == PAUSE_PORTAL_TYPE:
                for gate, period_slot in (
                    day_intervals.get(period, {}).get("gates", {}).items()
                ):
                    if period_slot and slot in period_slot:
                        slots_by_gate.setdefault(gate, []).append(slot)
            else:
                slots_by_gate.setdefault(slot.gate, []).append(slot)
        return slots_by_gate

    @memoize
    def get_free_slots(self, booking_date, period="day"):
        """This will return the free slots divided by gate

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'gate1': [slot1],
         'gate2': [slot2, slot3],
        }
        """
        day_intervals_by_gate = self.get_day_intervals(booking_date)
        if not day_intervals_by_gate:
            return {}
        gates_by_period = day_intervals_by_gate.get(period, {}).get("gates", {})
        availability = {}
        for gate, interval in gates_by_period.items():
            if period == "day":
                intervals = [
                    day_intervals_by_gate.get("morning", {}).get("gates", {})[gate],
                    day_intervals_by_gate.get("afternoon", {}).get("gates", {})[gate],
                ]
            else:
                intervals = [interval]
            slots_by_gate = self.get_busy_slots(booking_date, period)
            availability.setdefault(gate, [])
            all_gate_slots = slots_by_gate.get(gate, [])
            pauses_slots = [
                x for x in all_gate_slots if x.context.portal_type == PAUSE_PORTAL_TYPE
            ]
            booking_slots = [
                x for x in all_gate_slots if x.context.portal_type != PAUSE_PORTAL_TYPE
            ]
            gate_slots = []
            gate_slots.extend(pauses_slots)
            for slot in booking_slots:
                skip = False
                for pause in pauses_slots:
                    if slot in pause:
                        # edge-case when there is a slot created inside a pause range.
                        # probably this is because the slot (booking) has been created before
                        # someone set the pause.
                        # the booking should be listed, but its slot can't appear here because
                        # could mess free slots calc.
                        skip = True
                        break
                if not skip:
                    gate_slots.append(slot)
            for interval in intervals:
                if interval:
                    if interval.upper_value and interval.lower_value:
                        availability[gate].extend(interval - sorted(gate_slots))
        return availability

    def get_freebusy_slots(self, booking_date, period="day"):
        """This will return all the slots (free and busy) divided by gate

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'gate1': [slot1],
         'gate2': [slot2, slot3],
        }
        """
        free = self.get_free_slots(booking_date, period)
        busy = self.get_busy_slots(booking_date, period)
        keys = set(list(free.keys()) + list(busy.keys()))
        res = dict((key, sorted(free.get(key, []) + busy.get(key, []))) for key in keys)
        return res

    def get_anonymous_slots(self, booking_date, period="day"):
        """This will return all the slots under the fake name
        anonymous_gate

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'anonymous_gate': [slot2, slot3],
        }
        """
        slots_by_gate = {"anonymous_gate": {}}
        intervals_by_gate = self.get_day_intervals(booking_date)
        if not intervals_by_gate:
            return slots_by_gate
        intervals_data = intervals_by_gate.get(period, {})
        if not intervals_data:
            return slots_by_gate
        interval = intervals_data.get("interval", [])
        if not interval or len(interval) == 0:
            return slots_by_gate
        start = interval.lower_value
        stop = interval.upper_value
        hours = set(3600 * i for i in range(24) if start <= i * 3600 <= stop)
        hours = sorted(hours.union(set((start, stop))))
        slots_number = len(hours) - 1
        slots = [BaseSlot(hours[i], hours[i + 1]) for i in range(slots_number)]
        slots_by_gate["anonymous_gate"] = slots
        return slots_by_gate

    @property
    @memoize
    def booking_type_durations(self):
        """The durations of all known tipologies

        @return a dict like this:
        {'booking_type1': 10,
         'booking_type2': 20,
         ...
        }
        """

        return {
            typ.title: typ.duration
            for typ in self.context.get_booking_types()
            if typ.duration
        }

    def get_booking_type_duration(self, booking_type):
        """Return the seconds for this booking_type"""
        if type(booking_type) is PrenotazioneType:
            return int(booking_type.duration) * 60

        if type(booking_type) is str:
            return int(self.booking_type_durations.get(booking_type, 1))

        # XXX: se il booking_type non esiste, ritorna 1 minuto, è corretto ????
        return 1

    @memoize
    def booking_types_bookability(self, booking_date):
        """
        :param  booking_date: a datetime object

        Return a dictionary like this:
        {'bookable': ['booking_type 00', 'booking_type 01', ...],
         'unbookable': ['booking_type 10', 'booking_type 10', ...],
        }

        Bookability is calculated from the booking_date and the available slots
        """
        data = {"booking_date": booking_date}
        bookability = {"bookable": [], "unbookable": []}
        for booking_type in self.booking_type_durations:
            data["booking_type"] = booking_type
            if self.conflict_manager.conflicts(data):
                bookability["unbookable"].append(booking_type)
            else:
                bookability["bookable"].append(booking_type)
        return bookability

    @memoize
    def is_booking_date_bookable(self, booking_date):
        """Check if we have enough time to book this date

        :param booking_date: a date as a datetime
        """
        bookability = self.booking_types_bookability(booking_date)
        return bool(bookability["bookable"])

    def get_first_slot(self, booking_type, booking_date, period="day"):
        """
        The Prenotazione objects for today

        :param booking_type: a dict with name and duration
        :param booking_date: a date as a datetime or a string
        :param period: a DateTime object
        """
        if booking_date < self.first_bookable_date:
            return
        availability = self.get_free_slots(booking_date, period)
        good_slots = []
        duration = self.get_booking_type_duration(booking_type)

        hm_now = datetime.now().strftime("%H:%m")

        for slots in six.itervalues(availability):
            for slot in slots:
                if len(slot) >= duration and (
                    booking_date > self.first_bookable_date or slot.start() >= hm_now
                ):
                    good_slots.append(slot)
        if not good_slots:
            return
        good_slots.sort(key=lambda x: x.lower_value)
        return good_slots[0]

    def __call__(self):
        """Return itself"""
        return self

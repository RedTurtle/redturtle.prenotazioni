# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from plone import api
from plone.memoize.view import memoize
from Products.Five.browser import BrowserView
from redturtle.prenotazioni import _
from redturtle.prenotazioni import get_or_create_obj
from redturtle.prenotazioni import tznow
from redturtle.prenotazioni.config import PAUSE_SLOT, PAUSE_PORTAL_TYPE
from redturtle.prenotazioni.content.pause import Pause
from redturtle.prenotazioni.adapters.booker import IBooker
from redturtle.prenotazioni.adapters.conflict import IConflictManager
from redturtle.prenotazioni.adapters.slot import BaseSlot
from redturtle.prenotazioni.adapters.slot import ISlot
from redturtle.prenotazioni.utilities.urls import urlify
from six.moves import map
from six.moves import range


import six


def hm2handm(hm):
    """ This is a utility function that will return the hour and date of day
    to the value passed in the string hm

    :param hm: a string in the format "%H%m"
    """
    if (not hm) or (not isinstance(hm, six.string_types)) or (len(hm) != 4):
        raise ValueError(hm)
    return (hm[:2], hm[2:])


def hm2DT(day, hm):
    """ This is a utility function that will return the hour and date of day
    to the value passed in the string hm

    :param day: a datetime date
    :param hm: a string in the format "%H%m"
    """
    if not hm:
        return None
    date = day.strftime("%Y/%m/%d")
    h, m = hm2handm(hm)
    tzone = DateTime().timezone()
    return DateTime("%s %s:%s %s" % (date, h, m, tzone))


def hm2seconds(hm):
    """ This is a utility function that will return
    to the value passed in the string hm

    :param hm: a string in the format "%H%m"
    """
    if not hm:
        return None
    h, m = hm2handm(hm)
    return int(h) * 3600 + int(m) * 60


class PrenotazioniContextState(BrowserView):

    """
    This is a view to for checking prenotazioni context state
    """

    active_review_state = ["published", "pending"]
    add_view = "prenotazione_add"
    day_type = "PrenotazioniDay"
    week_type = "PrenotazioniWeek"
    year_type = "PrenotazioniYear"

    busy_slot_booking_url = {"url": "", "title": _("busy", u"Busy")}
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
    def user_permissions(self):
        """ The dict with the user permissions
        """
        return api.user.get_permissions(obj=self.context)

    @property
    @memoize
    def user_roles(self):
        """ The dict with the user permissions
        """
        return api.user.get_roles(obj=self.context)

    @property
    @memoize
    def user_can_manage(self):
        """ States if the authenticated user can manage this context
        """
        if self.is_anonymous:
            return False
        if self.user_permissions.get("Modify portal content", False):
            return True
        return False

    @property
    @memoize
    def user_can_view(self):
        """ States if the authenticated user can manage this context
        """
        if self.is_anonymous:
            return False
        if self.user_can_manage:
            return True
        if u"Reader" in self.user_roles:
            return True
        return False

    @property
    @memoize
    def user_can_search(self):
        """ States if the user can see the search button
        """
        return self.user_can_manage

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
        """ Cache for today date
        """
        return date.today()

    @property
    @memoize
    def yesterday(self):
        """ Cache for today date
        """
        return self.today - timedelta(days=1)

    @property
    @memoize
    def tomorrow(self):
        """ Cache for today date
        """
        return self.today + timedelta(days=1)

    @property
    @memoize
    def same_day_booking_allowed(self):
        """ State if the same day booking is allowed
        """
        value = getattr(self.context, "same_day_booking_disallowed")
        return value == "no" or value == self.today.strftime("%Y/%m/%d")

    @property
    @memoize
    def first_bookable_day(self):
        """ The first day when you can book stuff

        ;return; a datetime.date object
        """
        if self.same_day_booking_allowed:
            return max(self.context.getDaData(), self.today)
        return max(self.context.getDaData(), self.tomorrow)

    @property
    @memoize
    def last_bookable_day(self):
        """ The last day (if set) when you can book stuff

        ;return; a datetime.date object or None
        """
        adata = self.context.getAData()
        if not adata:
            return
        return adata

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
        """ Returns True if the day has been configured
        """
        weekday = day.weekday()
        week_table = getattr(self.context, "week_table", {})
        day_table = week_table[weekday]
        return any(
            (
                day_table["morning_start"],
                day_table["morning_end"],
                day_table["afternoon_start"],
                day_table["afternoon_end"],
            )
        )

    def is_before_allowed_period(self, day):
        """ Returns True if the day is before the first bookable day
        """
        date_limit = self.minimum_bookable_date
        if not date_limit:
            return False
        if day <= date_limit.date():
            return True
        return False

    @memoize
    def is_valid_day(self, day):
        """ Returns True if the day is valid
        """
        if day < self.first_bookable_day:
            return False
        if self.is_vacation_day(day):
            return False
        if self.last_bookable_day and day > self.last_bookable_day:
            return False
        if self.is_before_allowed_period(day):
            return False
        return self.is_configured_day(day)

    @property
    @memoize
    def conflict_manager(self):
        """
        Return the conflict manager for this context
        """
        return IConflictManager(self.context.aq_inner)

    @memoize
    def get_state(self, context):
        """ Facade to the api get_state method
        """
        if not context:
            return
        if context.portal_type == PAUSE_PORTAL_TYPE:
            return PAUSE_SLOT
        return api.content.get_state(context)

    @property
    @memoize
    def remembered_params(self):
        """ We want to remember some parameters
        """
        params = dict(
            (key, value)
            for key, value in six.iteritems(self.request.form)
            if (
                value
                and key.startswith("form.")
                and not key.startswith("form.action")
                and key not in ("form.booking_date",)
                or key
                in ("disable_plone.leftcolumn", "disable_plone.rightcolumn")
            )
        )
        for key, value in six.iteritems(params):
            if isinstance(value, six.text_type):
                params[key] = value
        return params

    @property
    @memoize
    def base_booking_url(self):
        """ Return the base booking url (no parameters) for this context
        """
        return "%s/%s" % (self.context.absolute_url(), self.add_view)

    def get_booking_urls(self, day, slot, slot_min_size=0, gate=None):
        """ Returns, if possible, the booking urls
        """
        # we have some conditions to check
        if not self.is_valid_day(day):
            return []
        if self.maximum_bookable_date:
            if day > self.maximum_bookable_date.date():
                return []
        date = day.strftime("%Y-%m-%d")
        params = self.remembered_params.copy()
        times = slot.get_values_hr_every(300, slot_min_size=slot_min_size)
        base_url = self.base_booking_url
        urls = []
        now_str = tznow().strftime("%Y-%m-%d %H:%M")
        for t in times:
            form_booking_date = " ".join((date, t))
            params["form.booking_date"] = form_booking_date
            if gate:
                params["gate"] = gate
            booking_date = DateTime(
                params["form.booking_date"]
            ).asdatetime()  # noqa
            urls.append(
                {
                    "title": t,
                    "url": urlify(base_url, params=params),
                    "class": t.endswith(":00") and "oclock" or None,
                    "booking_date": booking_date,
                    "future": (now_str <= form_booking_date),
                }
            )
        return urls

    def get_all_booking_urls_by_gate(self, day, slot_min_size=0):
        """ Get all the booking urls divided by gate
        """
        slots_by_gate = self.get_free_slots(day)
        urls = {}
        for gate in slots_by_gate:
            slots = slots_by_gate[gate]
            for slot in slots:
                slot_urls = self.get_booking_urls(
                    day, slot, slot_min_size=slot_min_size
                )
                urls.setdefault(gate, []).extend(slot_urls)
        return urls

    def get_all_booking_urls(self, day, slot_min_size=0):
        """ Get all the booking urls

        Not divided by gate
        """
        urls_by_gate = self.get_all_booking_urls_by_gate(day, slot_min_size)
        urls = {}
        for gate in urls_by_gate:
            for url in urls_by_gate[gate]:
                urls[url["title"]] = url
        return sorted(six.itervalues(urls), key=lambda x: x["title"])

    def is_slot_busy(self, day, slot):
        """ Check if a slot is busy (i.e. the is no free slot overlapping it)
        """
        free_slots = self.get_free_slots(day)
        for gate in free_slots:
            for free_slot in free_slots[gate]:
                intersection = slot.intersect(free_slot)
                if intersection:
                    if intersection.lower_value != intersection.upper_value:
                        return False
        return True

    @memoize
    def get_anonymous_booking_url(self, day, slot, slot_min_size=0):
        """ Returns, the the booking url for an anonymous user
        """
        # First we check if we have booking urls
        all_booking_urls = self.get_all_booking_urls(day, slot_min_size)
        if not all_booking_urls:
            # If not the slot can be unavailable or busy
            if self.is_slot_busy(day, slot):
                return self.busy_slot_booking_url
            else:
                return self.unavailable_slot_booking_url
        # Otherwise we check if the URL fits the slot boundaries
        slot_start = slot.start()
        slot_stop = slot.stop()

        for booking_url in all_booking_urls:
            if slot_start <= booking_url["title"] < slot_stop:
                if self.is_booking_date_bookable(booking_url["booking_date"]):
                    return booking_url
        return self.unavailable_slot_booking_url

    @memoize
    def get_gates(self):
        """
        Get's the gates, available and unavailable
        """
        return self.context.getGates() or [""]

    @memoize
    def get_unavailable_gates(self):
        """
        Get's the gates declared unavailable
        """
        return self.context.getUnavailable_gates()

    @memoize
    def get_available_gates(self):
        """
        Get's the gates declared available
        """
        total = set(self.get_gates())
        if self.get_unavailable_gates():
            unavailable = set(self.get_unavailable_gates())
        else:
            unavailable = set()
        return total - unavailable

    def get_busy_gates_in_slot(self, booking_date, booking_end_date=None):
        """
        The gates already associated to a Prenotazione object for booking_date

        :param booking_date: a DateTime object
        """
        active_review_states = ["published", "pending"]
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
        # unavailable gates are always busy
        if self.get_unavailable_gates():
            gates.update(self.get_unavailable_gates())
        return gates

    def get_full_gates_in_date(
        self, prenotazioni, booking_date, booking_end_date=None
    ):  # noqa
        gates = set()
        for brain in prenotazioni:
            prenotazione = brain._unrestrictedGetObject()
            start = prenotazione.getData_prenotazione()
            end = prenotazione.getData_scadenza()
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
        available = set(self.get_available_gates())
        busy = set(self.get_busy_gates_in_slot(booking_date, booking_end_date))
        return available - busy

    @memoize
    def get_day_intervals(self, day):
        """ Return the time ranges of this day
        """
        weekday = day.weekday()
        week_table = getattr(self.context, "week_table", {})
        day_table = week_table[weekday]
        # Convert hours to DateTime
        morning_start = hm2DT(day, day_table["morning_start"])
        morning_end = hm2DT(day, day_table["morning_end"])
        afternoon_start = hm2DT(day, day_table["afternoon_start"])
        afternoon_end = hm2DT(day, day_table["afternoon_end"])
        # Get's the daily schedule
        day_start = morning_start or afternoon_start
        day_end = afternoon_end or morning_end
        break_start = morning_end or afternoon_end
        break_stop = afternoon_start or morning_end
        return {
            "morning": BaseSlot(morning_start, morning_end),
            "break": BaseSlot(break_start, break_stop),
            "afternoon": BaseSlot(afternoon_start, afternoon_end),
            "day": BaseSlot(day_start, day_end),
            "stormynight": BaseSlot(0, 86400),
        }

    @property
    @memoize
    def weektable_boundaries(self):
        """ Return the boundaries to draw the week table

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
            "morning": BaseSlot(
                boundaries["morning_start"], boundaries["morning_end"]
            ),
            "afternoon": BaseSlot(
                boundaries["afternoon_start"], boundaries["afternoon_end"]
            ),
        }

    @property
    @memoize
    def maximum_bookable_date(self):
        """ Return the maximum bookable date

        return a datetime or None
        """
        future_days = self.context.getFutureDays()
        if not future_days:
            return
        date_limit = tznow() + timedelta(future_days)
        return date_limit

    @property
    @memoize
    def minimum_bookable_date(self):
        """ Return the minimum bookable date

        return a datetime or None
        """
        notbefore_days = self.context.getNotBeforeDays()
        if not notbefore_days:
            return
        date_limit = tznow() + timedelta(notbefore_days)
        return date_limit

    def get_container(self, booking_date, create_missing=False):
        """ Return the container for bookings in this date

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
            key=lambda x: (x.getData_prenotazione(), x.getData_scadenza())
        )
        return bookings

    @memoize
    def get_pauses_in_day_folder(self, booking_date):
        """
        This method takes all pauses from the week table and convert it on slot
        :param booking_date: a date as a datetime or a string
        """
        weekday = booking_date.weekday()
        pause_table = self.context.pause_table
        today_pauses = [row for row in pause_table if row["day"] == weekday]
        pauses = []
        if today_pauses:
            for pause in today_pauses:
                pause = Pause(
                    pause["pause_start"][:2] + ":" + pause["pause_start"][2:],
                    pause["pause_end"][:2] + ":" + pause["pause_end"][2:],
                    "",
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
        bookins_list = list(map(ISlot, bookings))
        pauses_list = list(map(ISlot, pauses))
        return bookins_list + pauses_list

    def get_busy_slots_in_stormynight(self, booking_date):
        """ This will show the slots that will not show elsewhere
        """
        morning_slots = self.get_busy_slots_in_period(booking_date, "morning")
        afternoon_slots = self.get_busy_slots_in_period(
            booking_date, "afternoon"
        )
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
        interval = self.get_day_intervals(booking_date)[period]
        if interval.start() == "" and interval.stop() == "":
            return []
        allowed_review_states = ["pending", "published", PAUSE_SLOT]
        # all slots
        slots = self.get_existing_slots_in_day_folder(booking_date)
        # the ones in the interval
        slots = [slot for slot in slots if slot in interval]
        # the one with the allowed review_state
        slots = [
            slot
            for slot in slots
            if self.get_state(slot.context) in allowed_review_states
        ]
        return sorted(slots)

    @memoize
    def get_busy_slots(self, booking_date, period="day"):
        """ This will return the busy slots divided by gate:

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'gate1': [slot1],
         'gate2': [slot2, slot3],
        }
        """
        slots_by_gate = {}
        slots = self.get_busy_slots_in_period(booking_date, period)
        for slot in slots:
            if slot.context.portal_type == PAUSE_PORTAL_TYPE:
                for gate in self.get_gates():
                    slots_by_gate.setdefault(gate, []).append(slot)
            else:
                slots_by_gate.setdefault(slot.gate, []).append(slot)
        return slots_by_gate

    @memoize
    def get_free_slots(self, booking_date, period="day"):
        """ This will return the free slots divided by gate

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'gate1': [slot1],
         'gate2': [slot2, slot3],
        }
        """
        day_intervals = self.get_day_intervals(booking_date)
        if period == "day":
            intervals = [day_intervals["morning"], day_intervals["afternoon"]]
        else:
            intervals = [day_intervals[period]]
        slots_by_gate = self.get_busy_slots(booking_date, period)
        gates = self.get_gates()
        availability = {}
        for gate in gates:
            # unavailable gates doesn't have free slots
            # XXX Riprendi da qui:
            if (
                self.get_unavailable_gates()
                and gate in self.get_unavailable_gates()
            ):
                availability[gate] = []
            else:
                availability.setdefault(gate, [])
                gate_slots = slots_by_gate.get(gate, [])
                for interval in intervals:
                    if interval:
                        availability[gate].extend(interval - gate_slots)
        return availability

    def get_freebusy_slots(self, booking_date, period="day"):
        """ This will return all the slots (free and busy) divided by gate

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
        return dict(
            (key, sorted(free.get(key, []) + busy.get(key, [])))
            for key in keys
        )

    def get_anonymous_slots(self, booking_date, period="day"):
        """ This will return all the slots under the fake name
        anonymous_gate

        :param booking_date: a datetime object
        :param period: a string
        :return: a dictionary like:
        {'anonymous_gate': [slot2, slot3],
        }
        """
        interval = self.get_day_intervals(booking_date)[period]
        slots_by_gate = {"anonymous_gate": []}
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
    def tipology_durations(self):
        """ The durations of all known tipologies

        @return a dict like this:
        {'tipology1': 10,
         'tipology2': 20,
         ...
        }
        """
        return dict(
            (x["name"], int(x["duration"]))
            for x in getattr(self.context, "booking_types", [])
        )

    def get_tipology_duration(self, tipology):
        """ Return the seconds for this tipology
        """
        if isinstance(tipology, dict):
            return int(tipology["duration"]) * 60
        if isinstance(tipology, six.string_types) and not isinstance(
            tipology, six.text_type
        ):
            tipology = tipology
        return self.tipology_durations.get(tipology, 1)

    @memoize
    def tipologies_bookability(self, booking_date):
        """
        :param  booking_date: a datetime object

        Return a dictionary like this:
        {'bookable': ['tipology 00', 'tipology 01', ...],
         'unbookable': ['tipology 10', 'tipology 10', ...],
        }

        Bookability is calculated from the booking_date and the available slots
        """
        data = {"booking_date": booking_date}
        bookability = {"bookable": [], "unbookable": []}
        for tipology in self.tipology_durations:
            data["tipology"] = tipology
            if self.conflict_manager.conflicts(data):
                bookability["unbookable"].append(tipology)
            else:
                bookability["bookable"].append(tipology)
        return bookability

    @memoize
    def is_booking_date_bookable(self, booking_date):
        """ Check if we have enough time to book this date

        :param booking_date: a date as a datetime
        """
        bookability = self.tipologies_bookability(booking_date)
        return bool(bookability["bookable"])

    def get_first_slot(self, tipology, booking_date, period="day"):
        """
        The Prenotazione objects for today

        :param tipology: a dict with name and duration
        :param booking_date: a date as a datetime or a string
        :param period: a DateTime object
        """
        if booking_date < self.first_bookable_date:
            return
        availability = self.get_free_slots(booking_date, period)
        good_slots = []
        duration = self.get_tipology_duration(tipology)

        hm_now = datetime.now().strftime("%H:%m")

        for slots in six.itervalues(availability):
            for slot in slots:
                if len(slot) >= duration and (
                    booking_date > self.first_bookable_date
                    or slot.start() >= hm_now
                ):
                    good_slots.append(slot)
        if not good_slots:
            return
        good_slots.sort(key=lambda x: x.lower_value)
        return good_slots[0]

    def get_less_used_gates(self, booking_date):
        """
        Find which gate is les busy the day of the booking
        """
        availability = self.get_free_slots(booking_date)
        # Create a dictionary where keys is the time the gate is free, and
        # value is a list of gates
        free_time_map = {}
        for gate, free_slots in six.iteritems(availability):
            free_time = sum(map(BaseSlot.__len__, free_slots))
            free_time_map.setdefault(free_time, []).append(gate)
        # Get a random choice among the less busy one
        max_free_time = max(free_time_map.keys())
        return free_time_map[max_free_time]

    def __call__(self):
        """ Return itself
        """
        return self

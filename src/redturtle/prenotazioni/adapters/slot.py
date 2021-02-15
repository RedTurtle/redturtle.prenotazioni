# -*- coding: utf-8 -*-
from DateTime import DateTime
from pyinter.interval import Interval
from six.moves import map
from six.moves import range
from zope.component import Interface
from zope.interface import implementer


def is_intervals_overlapping(intervals):
    """
    utility function to determine if in a list of intervals there is some
    overlapping.
    We could sort the intervals by start date. Then iterate the sublist of
    intervals starting from the second element.
    Iterating on this sublist, if the start of the current interval it's less
    than the end of the previous interval in the original sorted array, then
    we have overlap
    """
    if len(intervals) < 2:
        return False

    intervals_sorted_by_starts = sorted(intervals, key=lambda x: x[0])

    for i, interval in enumerate(intervals_sorted_by_starts[1:]):
        # we can use i 'cause skipping the first element, i always refer to
        # the previous element in the original array
        if interval[0] < intervals_sorted_by_starts[i][1]:
            return True
    return False


def interval_is_contained(interval, lower_bound, upper_bound):
    """
    utility function to determine if an interval is contained between two
    bounds.
    :param interval: something like ['0700', '0800']
    :param lower_bound: something like '0700'
    :param upper_bound: something like '1300'

    Basically we use time interval to define that an office is open between two
    hours. we need to know if a given interval it's smaller and cointaned in
    the other.

    We assume that the start could coincide with lower_bound but not with the
    upper_bound. Viceversa the end could coincide with the upper_bound but not
    with the lower_bound.

    We also assume that we have an increasing interval
    """
    I0 = interval[0]
    I1 = interval[1]
    assert I0 < I1
    return (
        I0 >= lower_bound
        and I0 < upper_bound
        and I1 > lower_bound
        and I1 <= upper_bound
    )


def slots_to_points(slots):
    """ Return a list of point starting from the slots
    """
    points = []
    [points.extend([x.lower_value, x.upper_value]) for x in slots]
    return sorted(points)


class ISlot(Interface):

    """
    Interface for a Slot object
    """


class LowerEndpoint(int):

    """ Lower Endpoint
    """


class UpperEndpoint(int):

    """ Upper Endpoint
    """


@implementer(ISlot)
class BaseSlot(Interval):

    """ Overrides and simplifies pyinter.Interval
    """

    _lower = Interval.CLOSED
    _upper = Interval.CLOSED
    context = None
    gate = ""
    extra_css_styles = []

    @staticmethod
    def time2seconds(value):
        """
        Takes a value and converts it into seconds

        :param value: a datetime or DateTime object
        """
        if isinstance(value, int):
            return value
        if not value:
            return None
        if isinstance(value, DateTime):
            value = value.asdatetime()
        return value.hour * 60 * 60 + value.minute * 60 + value.second

    def __init__(self, start, stop, gate=""):
        """
        Initialize an BaseSlot
        :param start:
        :param stop:
        :param gate:
        """
        if start is not None:
            self._lower_value = LowerEndpoint(self.time2seconds(start))
        if stop is not None:
            self._upper_value = UpperEndpoint(self.time2seconds(stop))
        self.gate = gate

    def __len__(self):
        """ The length of this object
        """
        if (
            self._upper_value is None
            or self.lower_value is None
            or self.empty()
        ):
            return 0
        return self._upper_value - self.lower_value

    def __nonzero__(self):
        """ Check if this should be True
        """
        if isinstance(self._lower_value, int) and isinstance(
            self._upper_value, int
        ):
            return 1
        else:
            return 0

    def __sub__(self, value):
        """ Subtract something from this
        """
        if isinstance(value, Interval):
            value = [value]

        # We filter not overlapping intervals
        good_intervals = [x for x in value if x.overlaps(self)]
        points = slots_to_points(good_intervals)

        start = self.lower_value
        intervals = []
        for x in points:
            if isinstance(x, LowerEndpoint) and x > start:
                intervals.append(BaseSlot(start, x))
                # we raise the bar waiting for another stop
                start = self.upper_value
            elif isinstance(x, UpperEndpoint):
                start = x
        intervals.append(BaseSlot(start, self.upper_value))
        return intervals

    def value_hr(self, value):
        """ format value in a human readable fashion
        """
        if not value:
            return ""
        hour = str(value // 3600).zfill(2)
        minute = str(int((value % 3600) / 60)).zfill(2)
        return "%s:%s" % (hour, minute)

    def start(self):
        """ Return the starting time
        """
        return self.value_hr(self._lower_value)

    def stop(self):
        """ Return the starting time
        """
        return self.value_hr(self._upper_value)

    def get_offset(self, is_interval):
        """
        We have two case to handle

        In case we have a slot crossing over hours, we need to add a pixel for
        every hour we change. e.g. if we have pause or appointment between 8.45
        and 9.15 we need to add 1px.
        If we have pause or appointment between 8.55 and 10.05, we need to add
        2px.
        This is caused by the border we add when we draw under every free hour

        We check if we have context, so we are sure we are dealing with a pause
        or with a reserveation. Then we take start and stop that are human
        readable hours (like 8:00). With this we can take just hours splitting
        the string and then make a difference between stop and start.

        Second case. If we have BaseSlot we are drawing the gate columns. We
        need to add a pixel offset 'cause if we don't stop at the end of the
        hour, in the table the box with the hour is half cutted
        """
        if self.context:
            start = int(self.start().split(":")[0])
            stop = int(self.stop().split(":")[0])
            return (stop - start) * 1.0

        if is_interval:
            stop = self.stop().split(":")[1]
            if stop in ("15", "30", "45"):
                offset = {"15": 45.0, "30": 30.0, "45": 15.0}[stop]
                return offset
        return 0.0

    def css_styles(self, is_interval=False):
        """ the css styles for this slot

        The height of the interval in pixel is equal
        to the interval length in minnutes
        """
        styles = []
        if self._upper_value and self._lower_value:
            # we add 1px for each hour to account for the border
            # between the slots
            height = len(self) / 60 * 1.0 + len(self) / 3600
            offset = self.get_offset(is_interval)
            height = height + offset
            styles.append("height:%dpx" % height)
        styles.extend(self.extra_css_styles)
        return ";".join(styles)

    def get_values_hr_every(self, width, slot_min_size=0):
        """ This partitions this slot if pieces of length width and
        return the human readable value of the starts

        If slot is [0, 1000]

        calling this with width 300 will return
        ["00:00", "00:05", "00:10"]

        If slot_min_size is passed it will not return values whose distance
        from slot upper value is lower than this
        """
        number_of_parts = int(len(self) / width)
        values = set([])
        start = self.lower_value
        end = self.upper_value
        for i in range(number_of_parts):
            value = start + width * i
            if (end - value) >= slot_min_size:
                values.add(value)
        return list(map(self.value_hr, sorted(values)))


@implementer(ISlot)
class Slot(BaseSlot):
    def __eq__(self, other):
        """ We need to compare also the context before comparing the boundaries
        """
        return self.context == other.context and super(Slot, self).__eq__(
            other
        )

    def __init__(self, context):
        """
        @param context: a Prenotazione object
        """
        self.context = context
        BaseSlot.__init__(
            self,
            context.getData_prenotazione(),
            context.getData_scadenza(),
            getattr(self.context, "gate", ""),
        )

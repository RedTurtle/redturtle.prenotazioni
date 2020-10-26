# -*- coding: utf-8 -*-
from DateTime import DateTime
from pyinter.interval import Interval
from six.moves import map
from six.moves import range
from zope.component import Interface
from zope.interface import implementer


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

    def css_styles(self):
        """ the css styles for this slot

        The height of the interval in pixel is equal
        to the interval length in minnutes
        """
        styles = []
        if self._upper_value and self._lower_value:
            # we add 1px for each hour to account for the border
            # between the slots
            height = len(self) / 60 * 1.0 + len(self) / 3600
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

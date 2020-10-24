# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOTreeSet
from csv import writer
from datetime import date, datetime, timedelta
from io import StringIO
from json import dumps
from plone.memoize.view import memoize
from redturtle.prenotazioni import _
from redturtle.prenotazioni import prenotazioniFileLogger
from redturtle.prenotazioni import prenotazioniLogger as logger
from redturtle.prenotazioni.browser.base import BaseView as PrenotazioniBaseView
from time import mktime
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface
from zope.schema import Date, TextLine, ValidationError
import six


class InvalidDate(ValidationError):
    __doc__ = _("invalid_end:search_date", u"Invalid start or end date")


def check_date(value):
    """
    Check if the input date is correct
    """
    if isinstance(value, date):
        return True
    raise InvalidDate


class IQueryForm(Interface):
    """
    Interface for querying stuff
    """

    user = TextLine(title=_(u"label_user", "User"), default=u"", required=False)
    start = Date(
        title=_("label_start", u"Start date "),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        constraint=check_date,
        required=False,
    )
    end = Date(
        title=_("label_end", u"End date"),
        description=_(" format (YYYY-MM-DD)"),
        default=None,
        constraint=check_date,
        required=False,
    )


def date2timestamp(value, delta=0):
    """ Conerts a date in the format "%Y-%m-%d" to a unix timestamp
    """
    try:
        value = datetime.strptime(value, "%Y-%m-%d")
        value = value + timedelta(delta)
        return mktime(value.timetuple())
    except Exception as e:
        logger.exception(value)
        raise (e)


def timestamp2date(value, date_format="%Y/%m/%d %H:%M"):
    """ Converts a timestamp to date_format
    """
    return datetime.fromtimestamp(value).strftime(date_format)


class ContextForm(PrenotazioniBaseView):
    """
    Aggregates data from the booking folders below
    """

    logstorage_key = "redturtle.prenotazioni.logstorage"
    file_logger = prenotazioniFileLogger

    @property
    @memoize
    def logstorage(self):
        """ This is an annotation OOTreeSet where we can store log entries
        """
        annotations = IAnnotations(self.context)
        if self.logstorage_key not in annotations:
            annotations[self.logstorage_key] = OOTreeSet()
        return annotations[self.logstorage_key]

    def add_entry(self, entry):
        """ Add an entry to the logstorage
        """
        return self.logstorage.add(entry)

    def remove_entry(self, entry):
        """ Remove an entry from the logstorage
        """
        try:
            return self.logstorage.remove(entry)
        except KeyError:
            pass

    def csvencode(self, data, human_readable=False):
        """
        Converts an array of info to a proper cvs string

        If human_readable is set to True it will convert
        timestamps and uids
        """
        dummy_file = StringIO()
        cw = writer(dummy_file)
        for line in data:
            if human_readable:
                line[self._ei_date] = timestamp2date(line[self._ei_date])
                line[4] = self.uid_to_url(line[4])["url"]
                line.pop(3)
            for idx, value in enumerate(line):
                if isinstance(value, six.text_type):
                    line[idx] = value.encode("utf8")
            cw.writerow(line)
        return dummy_file.getvalue().strip("\r\n")

    def csvlog(self, data):
        """ Log something, dumping it on a file and storing it in the
        logstorage
        """
        encoded_data = self.csvencode([data])
        self.file_logger.info(encoded_data)
        self.add_entry(dumps(encoded_data))

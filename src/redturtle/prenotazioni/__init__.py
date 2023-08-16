# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from App.config import getConfiguration
from DateTime import DateTime
from datetime import datetime
from datetime import timedelta
from dateutil.tz.tz import tzutc
from logging import FileHandler
from logging import Formatter
from logging import getLogger
from plone import api
from plone.api.exc import UserNotFoundError
from plone.app.event.base import default_timezone
from six.moves import map
from zope.i18nmessageid import MessageFactory

import pytz
import dateutil

logger = getLogger("redturtle.prenotazioni")
_ = MessageFactory("redturtle.prenotazioni")

prenotazioniMessageFactory = MessageFactory("redturtle.prenotazioni")
prenotazioniFileLogger = getLogger("redturtle.prenotazioni.file")


def tznow():
    """Return a timezone aware now"""
    tz = pytz.timezone(default_timezone())
    return datetime.now().astimezone(tz)


def datetime_with_tz(date_str):
    """
    Return a datetime timezone aware
    """
    if isinstance(date_str, datetime):
        date = date_str
    elif isinstance(date_str, DateTime):
        date = date_str.asdatetime()
    else:
        try:
            date = dateutil.parser.parse(date_str)
        except ValueError:
            raise ValueError(f"Invalid date: {date_str}")

    if date.tzinfo is None or isinstance(date.tzinfo, tzutc):
        tz = pytz.timezone(default_timezone())
        date = date.astimezone(tz)
    return date


def time2timedelta(value):
    """
    Transform the value in a timedelta object
    value is supposed to be in the format HH(.*)MM
    """
    hours, minutes = list(map(int, (value[0:2], value[-2:])))
    return timedelta(hours=hours, minutes=minutes)


def get_or_create_obj(folder, key, portal_type):
    """
    Get the object with id key from folder
    If it does not exist create an object with the given key and portal_type

    :param folder: a Plone folderish object
    :param key: the key of the child object
    :param portal_type: the portal_type of the child object
    """
    if key in folder:
        return folder[key]

    try:
        userid = folder.getOwner().getId()
        if not userid:
            raise UserNotFoundError()
        with api.env.adopt_user(userid):
            return api.content.create(type=portal_type, title=key, container=folder)
    except (UserNotFoundError, Unauthorized):
        with api.env.adopt_roles(["Manager"]):
            return api.content.create(type=portal_type, title=key, container=folder)


def init_handler():
    """
    Protect the namespace
    """
    if prenotazioniFileLogger.handlers:
        return
    product_config = getattr(getConfiguration(), "product_config", {})
    config = product_config.get("redturtle.prenotazioni", {})
    logfile = config.get("logfile")
    if not logfile:
        return
    hdlr = FileHandler(logfile)
    formatter = Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    hdlr.setFormatter(formatter)
    prenotazioniFileLogger.addHandler(hdlr)


init_handler()

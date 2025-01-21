# -*- coding: utf-8 -*-
from plone import api
from plone.registry.interfaces import IRegistry
from redturtle.prenotazioni import logger
from zope.component import getUtility


def send_email(msg):
    if not msg:
        logger.error("Could not send email due to no message was provided")
        return

    host = api.portal.get_tool(name="MailHost")
    registry = getUtility(IRegistry)
    encoding = registry.get("plone.email_charset", "utf-8")

    host.send(msg, charset=encoding)

# -*- coding: utf-8 -*-
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker
from zope.interface import alsoProvides
from zExceptions import BadRequest


class AddVacation(Service):
    def reply(self):
        data = json_body(self.request)

        alsoProvides(self.request, IDisableCSRFProtection)
        booker = IBooker(self.context.aq_inner)

        try:
            booker.create_vacation(data=data)
        except BookerException as e:
            raise BadRequest(e.args[0])
        self.reply_no_content()

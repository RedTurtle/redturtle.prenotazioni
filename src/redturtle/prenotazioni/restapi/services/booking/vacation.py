# -*- coding: utf-8 -*-

# #### DEPRECATED ####

from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.interface import alsoProvides

from redturtle.prenotazioni import _
from redturtle.prenotazioni.adapters.booker import BookerException
from redturtle.prenotazioni.adapters.booker import IBooker


class AddVacation(Service):
    def reply(self):
        data = json_body(self.request)
        alsoProvides(self.request, IDisableCSRFProtection)
        booker = IBooker(self.context.aq_inner)
        try:
            nslots = booker.create_vacation(data=data)
        except BookerException as e:
            raise BadRequest(e.args[0])
        if not nslots:
            raise BadRequest(
                _("Nessuno slot creato, verificare la corretteza dei dati inseriti")
            )
        self.reply_no_content()

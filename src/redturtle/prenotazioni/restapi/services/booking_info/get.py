# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from AccessControl import Unauthorized


class BookingInfo(Service):
    def reply(self):
        catalog = api.portal.get_tool("portal_catalog")

        query = {"portal_type": "Prenotazione", "UID": self.request.uid}
        booking = catalog.unrestrictedSearchResults(query)
        booking = booking[0]._unrestrictedGetObject()

        if api.user.is_anonymous():
            if booking.Creator():
                raise Unauthorized
        else:
            current_user = api.user.get_current()

            if (
                not api.user.has_permission(
                    "redturtle.prenotazioni.ManagePrenotazioni",
                    username=current_user.getUserName(),
                )
                and not booking.Creator() == current_user.getUserName()
            ):
                raise Unauthorized

        response = getMultiAdapter((booking, self.request), ISerializeToJson)()

        return response

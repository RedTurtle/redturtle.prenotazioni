# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class BookingInfo(Service):
    booking_uid = None

    def publishTraverse(self, request, booking_uid):
        if self.booking_uid is None:
            self.booking_uid = booking_uid
        return self

    def reply(self):
        if not self.booking_uid:
            return self.reply_no_content(status=404)
        catalog = api.portal.get_tool("portal_catalog")
        query = {"portal_type": "Prenotazione", "UID": self.booking_uid}
        booking = catalog.unrestrictedSearchResults(query)

        if not booking:
            return self.reply_no_content(status=404)

        booking = booking[0]._unrestrictedGetObject()
        if not booking.canAccessBooking():
            raise Unauthorized

        response = getMultiAdapter((booking, self.request), ISerializeToJson)()

        return response

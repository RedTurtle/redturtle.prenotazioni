# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from AccessControl import Unauthorized


class BookingInfo(Service):
    def reply(self):
        catalog = api.portal.get_tool("portal_catalog")
        booking = catalog(**{"UID": self.request.uid})[0]
        if not api.user.is_anonymous():
            current_user = api.user.get_current()
            if (
                not booking.Creator
                and api.user.has_permission(
                    "redturtle.prenotazioni.ManagePrenotazioni",
                    username=current_user.getUserName(),
                )
            ) or booking.Creator == current_user.getUserName():
                response = getMultiAdapter(
                    (booking.getObject(), self.request), ISerializeToJson
                )()
            else:
                raise Unauthorized

        # if api.user.is_anonymous():
        #     with api.env.adopt_roles(["Manager", "Member"]):
        #         res = api.content.find(UID=self.request.uid)
        #         brains = catalog(**{"UID": self.request.uid})[0]
        # else:
        #     brains = catalog(**{"UID": self.request.uid})[0]

        # response = getMultiAdapter(
        #     (booking.getObject(), self.request), ISerializeToJson
        # )()

        return response

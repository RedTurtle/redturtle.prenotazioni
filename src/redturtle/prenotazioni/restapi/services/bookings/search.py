# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.services import Service
from redturtle.prenotazioni.interfaces import ISerializeToPrenotazioneSearchableItem
from zExceptions import Unauthorized
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class BookingsSearch(Service):
    """
    Preonotazioni search view
    """

    def publishTraverse(self, request, userid):
        if not request.get("userid", None):
            request.set("userid", userid)
        return self

    def reply(self):
        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)

        if api.user.is_anonymous():
            raise Unauthorized("You must be logged in to perform this action")
        elif api.user.has_permission("redturtle.prenotazioni: search prenotazioni"):
            userid = self.request.get("userid", None)
        else:
            userid = api.user.get_current().getUserId()

        response = {"id": self.context.absolute_url() + "/@bookings"}
        query = {
            "portal_type": "Prenotazione",
        }

        if start_date or end_date:
            query["Date"] = {
                "query": [DateTime(i) for i in [start_date, end_date] if i],
                "range": f"{start_date and 'min' or ''}{start_date and end_date and ':' or ''}{end_date and 'max' or ''}",  # noqa: E501
            }

        if userid:
            query["fiscalcode"] = userid

        response["items"] = [
            getMultiAdapter(
                (i.getObject(), self.request),
                ISerializeToPrenotazioneSearchableItem,
            )()
            for i in api.portal.get_tool("portal_catalog")(**query)
        ]
        response["items_total"] = len(response["items"])

        return response

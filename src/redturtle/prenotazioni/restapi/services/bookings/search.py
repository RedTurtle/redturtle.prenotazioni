# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.services import Service
from redturtle.prenotazioni.interfaces import (
    ISerializeToPrenotazioneSearchableItem,
)
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

    def query(self):
        query = {"portal_type": "Prenotazione"}

        if api.user.is_anonymous():
            raise Unauthorized("You must be logged in to perform this action")
        elif api.user.has_permission(
            "redturtle.prenotazioni: search prenotazioni"
        ):
            userid = self.request.get("userid", None)
        else:
            userid = api.user.get_current().getUserId()

        if userid:
            query["fiscalcode"] = userid.upper()

        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)
        gate = self.request.get("gate", None)

        if start_date or end_date:
            query["Date"] = {
                "query": [DateTime(i) for i in [start_date, end_date] if i],
                "range": f"{start_date and 'min' or ''}{start_date and end_date and ':' or ''}{end_date and 'max' or ''}",  # noqa: E501
            }

        if gate:
            query["gate"] = gate

        return query

    def reply(self):
        response = {"id": self.context.absolute_url() + "/@bookings"}
        query = self.query()
        response["items"] = [
            getMultiAdapter(
                (i.getObject(), self.request),
                ISerializeToPrenotazioneSearchableItem,
            )()
            for i in api.portal.get_tool("portal_catalog")(**query)
        ]
        response["items_total"] = len(response["items"])

        return response


class BookingsSearchFolder(BookingsSearch):
    def query(self):
        query = super(BookingsSearchFolder, self).query()
        query["path"] = "/".join(self.context.getPhysicalPath())
        return query

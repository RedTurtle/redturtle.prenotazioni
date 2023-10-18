# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.services import Service
from zExceptions import Unauthorized
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from redturtle.prenotazioni.interfaces import ISerializeToPrenotazioneSearchableItem


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
        query = {
            "portal_type": "Prenotazione",
            "sort_on": "Date",
            "sort_order": "reverse",
        }

        if api.user.is_anonymous():
            raise Unauthorized("You must be logged in to perform this action")
        elif api.user.has_permission(
            "redturtle.prenotazioni: search prenotazioni", obj=self.context
        ):
            userid = self.request.get("userid", None)
        else:
            userid = api.user.get_current().getUserId()

        if userid:
            query["fiscalcode"] = userid.upper()

        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)
        gate = self.request.get("gate", None)
        booking_type = self.request.get("booking_type", None)
        SearchableText = self.request.get("SearchableText", None)
        review_state = self.request.get("review_state", None)

        # 2023-01-01 -> 2023-01-01T00:00:00
        if start_date and len(start_date) == 10:
            start_date = f"{start_date}T00:00:00"
        if end_date and len(end_date) == 10:
            end_date = f"{end_date}T23:59:59"
        if start_date or end_date:
            query["Date"] = {
                "query": [DateTime(i) for i in [start_date, end_date] if i],
                "range": f"{start_date and 'min' or ''}{start_date and end_date and ':' or ''}{end_date and 'max' or ''}",  # noqa: E501
            }

        if gate:
            query["Subject"] = "Gate: {}".format(gate)

        if booking_type:
            query["booking_type"] = booking_type

        if SearchableText:
            query["SearchableText"] = SearchableText

        if review_state:
            query["review_state"] = review_state

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

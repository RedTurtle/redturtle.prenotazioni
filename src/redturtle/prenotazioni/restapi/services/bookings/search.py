# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from redturtle.prenotazioni.interfaces import (
    ISerializeToPrenotazioneSearchableItem,
)


@implementer(IPublishTraverse)
class BookingsSearch(Service):
    """
    Preonotazioni search view
    """

    def publishTraverse(self, request, fiscalcode):
        if not request.get("fiscalcode", None):
            request.set("fiscalcode", fiscalcode)
        return self

    def reply(self):
        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)
        fiscalcode = self.request.get("fiscalcode", None)
        response = {"id": self.context.absolute_url() + "/@bookings"}
        query = {
            "portal_type": "Prenotazione",
        }

        if start_date or end_date:
            query["Date"] = {
                "query": [DateTime(i) for i in [start_date, end_date] if i],
                "range": f"{start_date and 'min' or ''}{start_date and end_date and ':' or ''}{end_date and 'max' or ''}",
            }

        if fiscalcode:
            query["fiscalcode"] = fiscalcode

        response["items"] = [
            getMultiAdapter(
                (i.getObject(), self.request),
                ISerializeToPrenotazioneSearchableItem,
            )()
            for i in api.portal.get_tool("portal_catalog")(**query)
        ]
        response["items_total"] = len(response["items"])

        return response

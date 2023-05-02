# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from zope.component import getMultiAdapter


class BookingsSearch(Service):
    """
    Preonotazioni search view
    """

    def reply(self):
        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)
        fiscalcode = self.request.get("fiscalcode", None)

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

        results = getMultiAdapter(
            (api.portal.get_tool("portal_catalog")(**query), self.request),
            ISerializeToJson,
        )(fullobjects=self.request.form.get("fullobjects", False))

        return results

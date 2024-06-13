# -*- coding: utf-8 -*-
import logging
import os

from DateTime import DateTime
from plone import api
from plone.restapi.services import Service
from zExceptions import Unauthorized
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from redturtle.prenotazioni.interfaces import ISerializeToPrenotazioneSearchableItem

logger = logging.getLogger(__name__)
SEE_OWN_ANONYMOUS_BOOKINGS = os.environ.get("SEE_OWN_ANONYMOUS_BOOKINGS") in [
    "True",
    "true",
    "1",
]


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
        sort_on = self.request.get("sort_on") or "Date"
        sort_order = self.request.get("sort_order") or "descending"
        query = {
            "portal_type": "Prenotazione",
            "sort_on": sort_on,
            "sort_order": sort_order,
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
            if userid.lower().startswith("tinit-") and userid[6:]:
                # search for both the original and the prefixed fiscalcode
                query["fiscalcode"] = [userid.upper(), userid[6:].upper()]
            else:
                query["fiscalcode"] = userid.upper()

        start_date = self.request.get("from", None)
        end_date = self.request.get("to", None)
        gate = self.request.get("gate", None)
        booking_type = self.request.get("booking_type", None)
        SearchableText = self.request.get("SearchableText", None)
        review_state = self.request.get("review_state", None)
        modified_after = self.request.get("modified_after", None)
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
        if modified_after:
            query["modified"] = {"query": DateTime(modified_after), "range": "min"}
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
        # XXX: `fullobjects` the correct behavior should be to use different serializers
        fullobjects = self.request.form.get("fullobjects", False) == "1"
        response = {"id": self.context.absolute_url() + "/@bookings"}
        query = self.query()
        items = []
        if query.get("fiscalcode") and SEE_OWN_ANONYMOUS_BOOKINGS:
            # brains = api.content.find(**query, unrestricted=True)
            brains = api.portal.get_tool("portal_catalog").unrestrictedSearchResults(
                **query
            )
            unrestricted = True
        else:
            # brains = api.content.find(**query)
            brains = api.portal.get_tool("portal_catalog")(**query)
            unrestricted = False
        for brain in brains:
            # TEMP: errors with broken catalog entries
            try:
                items.append(
                    getMultiAdapter(
                        (self.wrappedGetObject(brain, unrestricted), self.request),
                        ISerializeToPrenotazioneSearchableItem,
                    )(fullobjects=fullobjects)
                )
            except:  # noqa: E722
                logger.exception("error with %s", brain.getPath())
        response["items"] = items
        response["items_total"] = len(response["items"])
        return response

    @staticmethod
    def wrappedGetObject(brain, unrestricted=False):
        if unrestricted:
            # with api.env.adopt_user(brain.Creator):
            with api.env.adopt_roles("Manager"):
                return brain.getObject()
        return brain.getObject()


class BookingsSearchFolder(BookingsSearch):
    def query(self):
        query = super(BookingsSearchFolder, self).query()
        query["path"] = "/".join(self.context.getPhysicalPath())
        return query

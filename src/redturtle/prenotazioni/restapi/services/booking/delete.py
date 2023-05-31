# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class DeleteBooking(Service):
    booking_uid = None

    def publishTraverse(self, request, booking_uid):
        if self.booking_uid is None:
            self.booking_uid = booking_uid
        return self

    def reply(self):
        if not self.booking_uid:
            return self.reply_no_content(status=404)
        with api.env.adopt_roles(["Manager"]):
            booking = api.content.get(UID=self.booking_uid)
            if not booking:
                return self.reply_no_content(status=404)

        self.request.form["uid"] = self.booking_uid
        delete_view = api.content.get_view(
            name="confirm-delete",
            context=booking.getPrenotazioniFolder(),
            request=self.request,
        )
        res = delete_view.do_delete()
        if not res:
            # ok
            return self.reply_no_content()
        raise BadRequest(res.get("error", ""))

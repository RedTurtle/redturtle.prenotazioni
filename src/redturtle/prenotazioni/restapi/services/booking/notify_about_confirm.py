# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.services import Service
from Products.DCWorkflow.events import AfterTransitionEvent
from zExceptions import BadRequest
from zope.event import notify
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class NotifyUserAboutBookingConfirm(Service):
    booking_uid = None

    def publishTraverse(self, request, booking_uid):
        if self.booking_uid is None:
            self.booking_uid = booking_uid
        return self

    def reply(self):
        booking = api.content.get(UID=self.booking_uid)

        if not booking:
            raise BadRequest("Booking not found")

        transition_billet = type(
            "TranstionBillet", (object,), {"__name__": "confirm", "title": "Confirm"}
        )()

        notify(
            AfterTransitionEvent(
                workflow=None,
                obj=booking,
                old_state=None,
                new_state=None,
                status=None,
                kwargs=None,
                transition=transition_billet,
            )
        )

        return ""

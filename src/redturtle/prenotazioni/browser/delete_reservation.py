# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from datetime import datetime
from datetime import time
from plone import api
from plone.memoize.view import memoize
from plone.protect import CheckAuthenticator
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from redturtle.prenotazioni import _
from redturtle.prenotazioni import logger
from zExceptions import Forbidden
from zExceptions import NotFound
from zope.i18n import translate


class BaseView(BrowserView):
    @property
    @memoize
    def prenotazione(self):
        """
        Get's the prenotazione by uid
        """
        uid = self.request.get("uid")
        if not uid:
            return
        pc = getToolByName(self.context, "portal_catalog")
        query = {"portal_type": "Prenotazione", "UID": uid}
        brains = pc.unrestrictedSearchResults(query)
        if len(brains) != 1:
            return None

        return brains[0]._unrestrictedGetObject()

    def missing_uid_error(self):
        return translate(
            _("missing_uid", "You need to provide a reservation id."),
            context=self.request,
        )

    def missing_booking_error(self):
        return translate(
            _(
                "missing_booking",
                "Unable to find a booking with the givend id: ${uid}.",
                mapping={"uid": self.uid},
            ),
            context=self.request,
        )


class DeleteReservation(BaseView):
    """ """

    @property
    @memoize
    def label(self):
        """The label of this view"""
        title = self.context.Title()  # noqa
        return _(
            "delete_reservation_request",
            "Delete reservation request for: ${name}",
            mapping={"name": title},
        )

    def __call__(self):
        form = self.request.form
        self.uid = form.get("uid", None)
        if not self.uid:
            msg = self.missing_uid_error()
            api.portal.show_message(message=msg, type="warning", request=self.request)
            return self.request.response.redirect(self.context.absolute_url())
        if not self.prenotazione:
            msg = self.missing_booking_error()
            api.portal.show_message(message=msg, type="warning", request=self.request)
            return self.request.response.redirect(self.context.absolute_url())
        if not self.prenotazione.canDeleteBooking():
            raise Unauthorized
        return super(DeleteReservation, self).__call__()


class ConfirmDelete(BaseView):
    """
    Actually delete a reservation

    """

    def __call__(self):
        form = self.request.form
        self.uid = form.get("uid", None)

        try:
            CheckAuthenticator(self.request)
        except Forbidden:
            msg = translate(
                _(
                    "wrong_authenticator",
                    default="You tried to delete booking with a wrong action.",
                ),
                context=self.request,
            )
            api.portal.show_message(message=msg, type="error", request=self.request)
            return self.request.response.redirect(self.context.absolute_url())

        if not self.uid:
            msg = self.missing_uid_error()
            api.portal.show_message(message=msg, type="warning", request=self.request)
            return self.request.response.redirect(self.context.absolute_url())

        res = self.do_delete()
        if not res:
            msg = translate(
                _("booking_deleted_success", default="Your booking has been deleted."),
                context=self.request,
            )
            api.portal.show_message(message=msg, type="info", request=self.request)
        else:
            if res.get("error", ""):
                api.portal.show_message(
                    message=res["error"], type="error", request=self.request
                )
        return self.request.response.redirect(self.context.absolute_url())

    def do_delete(self):
        if not self.prenotazione:
            raise NotFound
        if not self.prenotazione.canDeleteBooking():
            raise Unauthorized

        now = datetime.now()
        expiration = datetime.combine(
            self.prenotazione.booking_date.date(), time(0, 0, 0)
        )

        if now > expiration and not self.prenotazione.isVacation():
            return {
                "error": translate(
                    _(
                        "delete_expired_booking",
                        "You can't delete your reservation; it's too late.",
                    ),
                    context=self.request,
                ),
            }
        if api.content.get_state(self.prenotazione) not in ("confirmed", "pending"):
            return {
                "error": translate(
                    _(
                        "delete_refused_booking",
                        "You can't delete your reservation.",
                    ),
                    context=self.request,
                ),
            }

        with api.env.adopt_roles(["Manager", "Member"]):
            try:
                api.content.transition(
                    self.prenotazione, "cancel"
                )  # , comment=_("Booking canceled"))
            except api.exc.InvalidParameterError:
                # TODO: backward compatibility, remove soon ----- >8 ----------------
                logger.exception(
                    "Please run the redturtle.prenotazioni upgrade step!",
                    self.booking_uid,
                )
                day_folder = self.prenotazione.aq_parent
                day_folder.manage_delObjects(self.prenotazione.id)

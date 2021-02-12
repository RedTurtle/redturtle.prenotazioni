# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from plone.memoize.view import memoize
from redturtle.prenotazioni import _
from plone import api
from redturtle.prenotazioni.adapters.prenotazione import IDeleteTokenProvider


class DeleteReservation(BrowserView):
    template = ViewPageTemplateFile("templates/delete_reservation.pt")

    @property
    @memoize
    def label(self):
        """ The lable of this view
        """
        title = self.context.Title()  # noqa
        return _(
            "delete_reservation_request",
            u"Delete reservation request for: ${name}",
            mapping={"name": title},
        )

    @property
    @memoize
    def no_reservation_label(self):
        """ The lable of this view when no reservation is found
        """
        title = self.context.Title()  # noqa
        return _("no_reservation", u"Seems your reservation is not existing",)

    @property
    @memoize
    def deleted_label(self):
        """ The lable of this view when reservation is deleted
        """
        title = self.context.Title()  # noqa
        return _("deleted_reservation", u"Your reservation has been deleted",)

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

    def say_status(self, msg, msg_type):
        msg = self.context.translate(msg, "redturtle.prenotazioni")
        api.portal.show_message(
            message=msg, type=msg_type, request=self.request
        )

    def delete_reservation(self):
        prenotazione = self.prenotazione
        if not prenotazione:
            self.say_status(
                _(
                    "You can't delete your reservation; please contact"
                    " the office"
                ),
                "error",
            )
            return
        adapter = IDeleteTokenProvider(prenotazione)
        is_valid_token = adapter.is_valid_token(self.delete_token)
        if is_valid_token == "invalid":
            self.say_status(
                _(
                    "You can't delete your reservation; please contact"
                    " the office"
                ),
                "error",
            )
        elif is_valid_token == "expired":
            self.say_status(
                _("You can't delete your reservation; it's too late"), "error"
            )

        else:
            with api.env.adopt_roles(["Manager", "Member"]):
                api.content.delete(obj=prenotazione)
                self.say_status(_("Your reservation has been deleted"), "info")

    def __call__(self):

        form = self.request.form
        self.uid = form.get("uid", None)
        self.delete_token = form.get("delete_token", None)
        self.confirm = form.get("confirm", None)
        self.deleted_procedure_ended = False
        if self.confirm:
            self.delete_reservation()
            self.deleted_procedure_ended = True
        if not self.uid or not self.delete_token:
            msg = _("Some information to delete your reservation is missing")
            msg = self.context.translate(msg, "redturtle.prenotazioni")
            api.portal.show_message(
                message=msg, type="error", request=self.request
            )
        return self.template()

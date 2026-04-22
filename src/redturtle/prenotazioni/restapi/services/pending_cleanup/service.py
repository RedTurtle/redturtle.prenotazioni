# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.services import Service
from redturtle.prenotazioni import _
from redturtle.prenotazioni.utilities.pending_cleanup import (
    cleanup_pending_bookings_in_folder,
)
from redturtle.prenotazioni.utilities.pending_cleanup import (
    cleanup_pending_bookings_in_site,
)
from transaction import commit
from zExceptions import Unauthorized


class PendingCleanupBase(Service):
    def ensure_manager_permissions(self):
        if not api.user.has_permission(
            "redturtle.prenotazioni: Manage Prenotazioni",
            obj=self.context,
        ):
            raise Unauthorized(
                api.portal.translate(
                    _(
                        "pending_cleanup_unauthorized",
                        default="You are not allowed to run pending cleanup",
                    ),
                    context=self.request,
                )
            )

    def is_dry_run(self):
        return self.request.get("dry_run", "1") in ("1", "true", "True")


class PendingCleanupSite(PendingCleanupBase):
    def reply(self):
        self.ensure_manager_permissions()

        dry_run = self.is_dry_run() if self.request.method == "GET" else False
        stats = cleanup_pending_bookings_in_site(dry_run=dry_run)

        if not dry_run:
            commit()

        return {
            "service": "@cleanup-pending-bookings",
            "scope": "site",
            "dry_run": dry_run,
            "stats": stats,
        }


class PendingCleanupFolder(PendingCleanupBase):
    def reply(self):
        self.ensure_manager_permissions()

        dry_run = self.is_dry_run() if self.request.method == "GET" else False
        stats = cleanup_pending_bookings_in_folder(self.context, dry_run=dry_run)

        if not dry_run:
            commit()

        return {
            "service": "@cleanup-pending-bookings",
            "scope": "folder",
            "dry_run": dry_run,
            "stats": stats,
        }

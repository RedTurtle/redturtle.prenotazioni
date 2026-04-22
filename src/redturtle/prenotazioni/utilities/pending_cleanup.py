# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from redturtle.prenotazioni import logger


def _get_folder_settings(folder):
    return {
        "enabled": bool(getattr(folder, "pending_bookings_cleanup_enabled", False)),
        "days": int(getattr(folder, "pending_bookings_cleanup_days", 0) or 0),
        "delete": bool(getattr(folder, "pending_bookings_cleanup_delete", False)),
        "notify_users": bool(
            getattr(folder, "pending_bookings_cleanup_notify_users", False)
        ),
    }


def _get_pending_brains(folder, days):
    cutoff = DateTime() - days
    return api.content.find(
        portal_type="Prenotazione",
        review_state="pending",
        path={"query": "/".join(folder.getPhysicalPath())},
        Date={"query": cutoff, "range": "max"},
        sort_on="created",
    )


def _transition_to_canceled(booking, notify_users):
    folder = booking.getPrenotazioniFolder()
    original_notify_on_cancel = bool(getattr(folder, "notify_on_cancel", False))
    changed_notify_flag = original_notify_on_cancel != notify_users

    if changed_notify_flag:
        folder.notify_on_cancel = notify_users

    try:
        if api.content.get_state(obj=booking, default=None) != "pending":
            return False

        workflow_tool = api.portal.get_tool("portal_workflow")
        available_transitions = {
            item.get("id") for item in workflow_tool.getTransitionsFor(booking)
        }
        if "cancel" not in available_transitions:
            logger.warning(
                f"Booking {booking.absolute_url()} cannot be canceled from current state."
            )
            return False

        api.content.transition(obj=booking, transition="cancel")
        booking.reindexObject(idxs=["review_state"])
        return True
    finally:
        if changed_notify_flag:
            folder.notify_on_cancel = original_notify_on_cancel


def cleanup_pending_bookings_in_folder(folder, dry_run=False):
    settings = _get_folder_settings(folder)
    results = {
        "folder_path": "/".join(folder.getPhysicalPath()),
        "enabled": settings["enabled"],
        "days": settings["days"],
        "delete": settings["delete"],
        "notify_users": settings["notify_users"],
        "dry_run": bool(dry_run),
        "matched": 0,
        "canceled": 0,
        "deleted": 0,
    }

    if not settings["enabled"]:
        return results

    if settings["days"] <= 0:
        logger.warning(
            "Pending cleanup is enabled for %s but threshold is invalid (%s).",
            results["folder_path"],
            settings["days"],
        )
        return results

    pending_brains = _get_pending_brains(folder=folder, days=settings["days"])
    results["matched"] = len(pending_brains)

    if dry_run:
        results["canceled"] = len(pending_brains)
        if settings["delete"]:
            results["deleted"] = len(pending_brains)
        return results

    for brain in pending_brains:
        booking = brain.getObject()

        if settings["delete"]:
            if settings["notify_users"]:
                if _transition_to_canceled(booking=booking, notify_users=True):
                    results["canceled"] += 1
            api.content.delete(obj=booking)
            results["deleted"] += 1
            continue

        if _transition_to_canceled(
            booking=booking,
            notify_users=settings["notify_users"],
        ):
            results["canceled"] += 1

    return results


def cleanup_pending_bookings_in_site(dry_run=False):
    totals = {
        "folders": 0,
        "matched": 0,
        "canceled": 0,
        "deleted": 0,
        "dry_run": bool(dry_run),
        "items": [],
    }

    for folder_brain in api.content.find(portal_type="PrenotazioniFolder"):
        folder = folder_brain.getObject()
        result = cleanup_pending_bookings_in_folder(folder, dry_run=dry_run)

        totals["folders"] += 1
        totals["matched"] += result["matched"]
        totals["canceled"] += result["canceled"]
        totals["deleted"] += result["deleted"]
        totals["items"].append(result)

    return totals

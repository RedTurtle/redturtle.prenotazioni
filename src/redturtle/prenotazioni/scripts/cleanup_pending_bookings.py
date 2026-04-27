# -*- coding: utf-8 -*-
"""Cleanup old pending bookings script."""

from DateTime import DateTime
from plone import api
from plone.api.exc import InvalidParameterError
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.content.prenotazioni_folder import IPrenotazioniFolder
from transaction import commit

import argparse
import sys


def _transition_to_canceled(booking, notify_users):
    folder = booking.getPrenotazioniFolder()
    original_notify_on_cancel = bool(getattr(folder, "notify_on_cancel", False))
    changed_notify_flag = original_notify_on_cancel != notify_users

    if changed_notify_flag:
        folder.notify_on_cancel = notify_users

    try:
        if api.content.get_state(obj=booking, default=None) != "pending":
            return False

        try:
            api.content.transition(obj=booking, transition="cancel")
        except InvalidParameterError:
            logger.warning(
                f"Booking {booking.absolute_url()} cannot be canceled from current state."
            )
            return False
        booking.reindexObject(idxs=["review_state"])
        return True
    finally:
        if changed_notify_flag:
            folder.notify_on_cancel = original_notify_on_cancel


def cleanup_pending_bookings_in_folder(folder):
    settings = {
        "enabled": bool(getattr(folder, "pending_bookings_cleanup_enabled", False)),
        "days": int(getattr(folder, "pending_bookings_cleanup_days", 0) or 0),
        "delete": bool(getattr(folder, "pending_bookings_cleanup_delete", False)),
        "notify_users": bool(
            getattr(folder, "pending_bookings_cleanup_notify_users", False)
        ),
    }
    results = {
        "folder_path": "/".join(folder.getPhysicalPath()),
        "enabled": settings["enabled"],
        "days": settings["days"],
        "delete": settings["delete"],
        "notify_users": settings["notify_users"],
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

    cutoff = DateTime() - settings["days"]
    pending_brains = api.content.find(
        object_provides=IPrenotazione.__identifier__,
        review_state="pending",
        context=folder,
        Date={"query": cutoff, "range": "max"},
    )
    results["matched"] = len(pending_brains)

    for brain in pending_brains:
        booking = brain.getObject()

        if settings["delete"]:
            api.content.delete(obj=booking)
            results["canceled"] += 1
            results["deleted"] += 1
            continue

        if _transition_to_canceled(
            booking=booking,
            notify_users=settings["notify_users"],
        ):
            results["canceled"] += 1

    return results


def cleanup_pending_bookings_in_site():
    totals = {
        "folders": 0,
        "matched": 0,
        "canceled": 0,
        "deleted": 0,
        "items": [],
    }

    for folder_brain in api.content.find(
        object_provides=IPrenotazioniFolder.__identifier__
    ):
        folder = folder_brain.getObject()
        result = cleanup_pending_bookings_in_folder(folder)

        totals["folders"] += 1
        totals["matched"] += result["matched"]
        totals["canceled"] += result["canceled"]
        totals["deleted"] += result["deleted"]
        totals["items"].append(result)

    return totals


def main():
    parser = argparse.ArgumentParser(description="Cleanup old pending bookings.")
    parser.add_argument(
        "--path",
        default=None,
        help="Physical path of a PrenotazioniFolder to process. "
        "If omitted, all folders in the site are processed.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="Commit the transaction at the end.",
    )
    args = parser.parse_args(sys.argv[1:])

    with api.env.adopt_roles(roles=["Manager"]):
        if args.path:
            folder = api.content.get(path=args.path)
            if folder is None:
                logger.error("No object found at path: %s", args.path)
                return
            if not IPrenotazioniFolder.providedBy(folder):
                logger.error(
                    "Object at %s is not a PrenotazioniFolder (got %s).",
                    args.path,
                    folder.__class__.__name__,
                )
                return
            result = cleanup_pending_bookings_in_folder(folder)
            stats = {
                "folders": 1,
                "matched": result["matched"],
                "canceled": result["canceled"],
                "deleted": result["deleted"],
            }
        else:
            stats = cleanup_pending_bookings_in_site()

    logger.info(
        "Pending cleanup done. Folders=%s matched=%s canceled=%s deleted=%s",
        stats["folders"],
        stats["matched"],
        stats["canceled"],
        stats["deleted"],
    )

    if args.commit:
        commit()


if __name__ == "__main__":
    main()  # noqa

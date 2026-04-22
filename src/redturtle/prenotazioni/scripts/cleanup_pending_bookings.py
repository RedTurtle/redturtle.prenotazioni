# -*- coding: utf-8 -*-
"""Cleanup old pending bookings script."""

from plone import api
from redturtle.prenotazioni import logger
from redturtle.prenotazioni.utilities.pending_cleanup import (
    cleanup_pending_bookings_in_site,
)
from transaction import commit


def main():
    with api.env.adopt_roles(roles=["Manager"]):
        stats = cleanup_pending_bookings_in_site()

    logger.info(
        "Pending cleanup done. Folders=%s matched=%s canceled=%s deleted=%s",
        stats["folders"],
        stats["matched"],
        stats["canceled"],
        stats["deleted"],
    )
    commit()


if __name__ == "__main__":
    main()  # noqa

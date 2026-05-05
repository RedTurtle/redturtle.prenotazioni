# -*- coding: utf-8 -*-
"""Send reminders script"""

from plone import api
from redturtle.prenotazioni import logger
from transaction import commit
from zope.globalrequest import getRequest


def main():
    with api.env.adopt_roles(roles=["Manager"]):
        logger.info("Call the send reminders view")
        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

    commit()


if __name__ == "__main__":
    main()  # noqa

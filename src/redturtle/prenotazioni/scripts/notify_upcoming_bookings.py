# -*- coding: utf-8 -*-
"""Send reminders script"""

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Testing.makerequest import makerequest
from transaction import commit
from zope.component.hooks import setHooks
from zope.component.hooks import setSite
from zope.globalrequest import getRequest

from redturtle.prenotazioni import logger


def main(app):
    app = makerequest(app)
    portal = app.Plone
    admin = app.acl_users.getUserById("admin")

    newSecurityManager(None, admin)
    setHooks()
    setSite(portal)

    with api.env.adopt_roles(roles=["Manager"]):
        logger.info("Call the send reminders view")
        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

    commit()


if __name__ == "__main__":
    main(app)  # noqa

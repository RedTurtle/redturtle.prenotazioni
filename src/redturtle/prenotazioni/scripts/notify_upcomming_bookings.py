# -*- coding: utf-8 -*-
"""Send reminders script"""

from logging import getLogger

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Testing.makerequest import makerequest
from transaction import commit
from zope.component.hooks import setHooks, setSite
from zope.globalrequest import getRequest

logger = getLogger(__name__)


def main(app):
    app = makerequest(app)
    portal = app.Plone
    admin = app.acl_users.getUserById("admin")

    newSecurityManager(None, admin)
    setHooks()
    setSite(portal)

    with api.env.adopt_user(username="admin"):
        logger.info("Call the send reminders view")
        api.content.get_view(
            context=api.portal.get(),
            request=getRequest(),
            name="send-booking-reminders",
        )()

    commit()


if __name__ == "__main__":
    main(app)  # noqa

# -*- coding: utf-8 -*-
import importlib.metadata

from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from zope.interface import Interface

HASH = importlib.metadata.version("redturtle.prenotazioni")


class HeadViewlet(ViewletBase):
    """TEMP: workaround for compatibility plone 5.2/6.0"""

    def portal_url(self):
        return api.portal.get().absolute_url()

    def hash(self):
        return HASH

    def render(self):
        return """
<link href="{portal_url}/++plone++redturtle.prenotazioni/redturtle-reservation.css?_={hash}" rel="stylesheet"></link>
<script src="{portal_url}/++plone++redturtle.prenotazioni/redturtle-reservation.js?_={hash}"></script>
        """.format(
            portal_url=self.portal_url(),
            hash=self.hash(),
        )


class IHasTableOverridesMarker(Interface):
    """marker interface"""


class HasTableOverridesWidget(HeadViewlet):
    """TEMP: workaround for compatibility plone 5.2/6.0"""

    def portal_url(self):
        return api.portal.get().absolute_url()

    def hash(self):
        return "0001"

    def render(self):
        return """
<link href="{portal_url}/++plone++redturtle.prenotazioni/widget/dist/{mode}/main.css?_={hash}" rel="stylesheet"></link>
<script src="{portal_url}/++plone++redturtle.prenotazioni/widget/dist/{mode}/main.js?_={hash}"></script>
        """.format(
            portal_url=self.portal_url(),
            mode="dev" if api.env.debug_mode() else "prod",
            hash=self.hash(),
        )

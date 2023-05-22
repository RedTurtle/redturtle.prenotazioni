# -*- coding: utf-8 -*-
from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from zope.interface import Interface


class IHasTableOverridesMarker(Interface):
    """ """


class HasTableOverridesWidget(ViewletBase):
    """ """

    def portal_url(self):
        return api.portal.get().absolute_url()

    def render(self):
        return """
<link href="{portal_url}/++plone++redturtle.prenotazioni/widget/dist/{mode}/main.css" rel="stylesheet"></link>
<script src="{portal_url}/++plone++redturtle.prenotazioni/widget/dist/{mode}/main.js"></script>
        """.format(
            portal_url=self.portal_url(),
            # mode="prod",
            mode="dev" if api.env.debug_mode() else "prod",
        )

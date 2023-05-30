# -*- coding: utf-8 -*-
from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "redturtle.prenotazioni:uninstall",
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.

    plone_version = api.env.plone_version()
    if plone_version < "6":
        portal_types = api.portal.get_tool(name="portal_types")
        behaviors = list(portal_types["PrenotazioniFolder"].behaviors)
        if "collective.dexteritytextindexer" in behaviors:
            return
        behaviors.append("collective.dexteritytextindexer")
        portal_types["PrenotazioniFolder"].behaviors = tuple(behaviors)


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.

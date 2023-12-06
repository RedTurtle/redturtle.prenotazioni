# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest

from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import ISearchSchema
from zope.component import getUtility

from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that redturtle.prenotazioni is properly installed."""

    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if redturtle.prenotazioni is installed."""
        if hasattr(self.installer, "is_product_installed"):
            # Plone 6
            self.assertTrue(
                self.installer.is_product_installed("redturtle.prenotazioni")
            )
        else:
            self.assertTrue(self.installer.isProductInstalled("redturtle.prenotazioni"))

    def test_browserlayer(self):
        """Test that IRedturtlePrenotazioniLayer is registered."""
        from plone.browserlayer import utils

        from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer

        self.assertIn(IRedturtlePrenotazioniLayer, utils.registered_layers())

    def test_dexteritytextindexer_behavior_enabled_only_in_plone_less_than_6(self):
        plone_version = api.env.plone_version()
        portal_types = api.portal.get_tool(name="portal_types")
        behaviors = portal_types["PrenotazioniFolder"].behaviors
        if plone_version < "6":
            self.assertIn("collective.dexteritytextindexer", behaviors)
        else:
            self.assertNotIn("collective.dexteritytextindexer", behaviors)

    def test_searchable_types(self):
        registry = getUtility(IRegistry)
        types_not_searched = registry.forInterface(
            ISearchSchema, prefix="plone"
        ).types_not_searched

        types = [
            "Prenotazione",
            "PrenotazioniDay",
            "PrenotazioniWeek",
            "PrenotazioniYear",
            "PrenotazioneType",
            "PrenotazioniFolder",
        ]
        for ptype in types:
            self.assertIn(ptype, types_not_searched)


class TestUninstall(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        if hasattr(self.installer, "uninstall_product"):
            # Plone 6
            self.installer.uninstall_product("redturtle.prenotazioni")
        else:
            self.installer.uninstallProducts(["redturtle.prenotazioni"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if redturtle.prenotazioni is cleanly uninstalled."""
        if hasattr(self.installer, "is_product_installed"):
            # Plone 6
            self.assertFalse(
                self.installer.is_product_installed("redturtle.prenotazioni")
            )
        else:
            self.assertFalse(
                self.installer.isProductInstalled("redturtle.prenotazioni")
            )

    def test_browserlayer_removed(self):
        """Test that IRedturtlePrenotazioniLayer is removed."""
        from plone.browserlayer import utils

        from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer

        self.assertNotIn(IRedturtlePrenotazioniLayer, utils.registered_layers())

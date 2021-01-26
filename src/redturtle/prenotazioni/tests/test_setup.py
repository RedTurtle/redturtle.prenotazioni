# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from redturtle.prenotazioni.testing import (
    REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING,
)  # noqa: E501

import unittest


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
        self.assertTrue(
            self.installer.isProductInstalled("redturtle.prenotazioni")
        )

    def test_browserlayer(self):
        """Test that IRedturtlePrenotazioniLayer is registered."""
        from plone.browserlayer import utils
        from redturtle.prenotazioni.interfaces import (
            IRedturtlePrenotazioniLayer,
        )

        self.assertIn(IRedturtlePrenotazioniLayer, utils.registered_layers())


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
        self.installer.uninstallProducts(["redturtle.prenotazioni"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if redturtle.prenotazioni is cleanly uninstalled."""
        self.assertFalse(
            self.installer.isProductInstalled("redturtle.prenotazioni")
        )

    def test_browserlayer_removed(self):
        """Test that IRedturtlePrenotazioniLayer is removed."""
        from plone.browserlayer import utils
        from redturtle.prenotazioni.interfaces import (
            IRedturtlePrenotazioniLayer,
        )

        self.assertNotIn(
            IRedturtlePrenotazioniLayer, utils.registered_layers()
        )

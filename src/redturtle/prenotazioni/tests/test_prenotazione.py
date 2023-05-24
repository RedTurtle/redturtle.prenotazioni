# -*- coding: utf-8 -*-
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.autoform.interfaces import MODES_KEY
from plone.restapi.testing import RelativeSession
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING
from redturtle.prenotazioni.testing import REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING
from zope.interface import Interface

import unittest


class TestSchemaDirectives(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING

    def test_field_modes(self):
        self.assertEqual(
            [
                (Interface, "booking_date", "display"),
                (Interface, "gate", "display"),
                (Interface, "booking_expiration_date", "display"),
            ],
            IPrenotazione.queryTaggedValue(MODES_KEY),
        )


class TestPrenotazioniRestAPIInfo(unittest.TestCase):
    layer = REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        self.api_session.close()

    def test_prenotazione_restapi_endpoint(self):
        result = self.api_session.get(self.portal_url + "/@types/Prenotazione")
        content_type_properties = result.json()["properties"]
        self.assertEqual(content_type_properties["booking_date"]["mode"], "display")
        self.assertEqual(content_type_properties["gate"]["mode"], "display")
        self.assertEqual(
            content_type_properties["booking_expiration_date"]["mode"], "display"
        )

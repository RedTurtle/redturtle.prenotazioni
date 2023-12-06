# -*- coding: utf-8 -*-
import collective.contentrules.mailfromfield
import collective.z3cform.datagridfield
import plone.app.caching
import plone.restapi
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import MOCK_MAILHOST_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.restapi.testing import PloneRestApiDXLayer
from plone.testing import z2

import redturtle.prenotazioni

try:
    import collective.dexteritytextindexer

    HAS_DX_TEXTINDEXER = True
except ImportError:
    HAS_DX_TEXTINDEXER = False


class RedturtlePrenotazioniLayer(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE, MOCK_MAILHOST_FIXTURE)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=plone.app.caching)
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.prenotazioni)
        self.loadZCML(package=collective.contentrules.mailfromfield)
        self.loadZCML(package=collective.z3cform.datagridfield)

        if HAS_DX_TEXTINDEXER:
            self.loadZCML(package=collective.dexteritytextindexer)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.caching:default")
        applyProfile(portal, "redturtle.prenotazioni:default")


REDTURTLE_PRENOTAZIONI_FIXTURE = RedturtlePrenotazioniLayer()


REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING = IntegrationTesting(
    bases=(REDTURTLE_PRENOTAZIONI_FIXTURE,),
    name="RedturtlePrenotazioniLayer:IntegrationTesting",
)


REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_PRENOTAZIONI_FIXTURE,),
    name="RedturtlePrenotazioniLayer:FunctionalTesting",
)


class RedturtlePrenotazioniRestApiLayer(PloneRestApiDXLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        super(RedturtlePrenotazioniRestApiLayer, self).setUpZope(
            app, configurationContext
        )

        self.loadZCML(package=plone.app.caching)
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.prenotazioni)
        self.loadZCML(package=collective.contentrules.mailfromfield)
        self.loadZCML(package=collective.z3cform.datagridfield)

        if HAS_DX_TEXTINDEXER:
            self.loadZCML(package=collective.dexteritytextindexer)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.caching:default")
        applyProfile(portal, "redturtle.prenotazioni:default")


REDTURTLE_PRENOTAZIONI_API_FIXTURE = RedturtlePrenotazioniRestApiLayer()
REDTURTLE_PRENOTAZIONI_API_INTEGRATION_TESTING = IntegrationTesting(
    bases=(REDTURTLE_PRENOTAZIONI_API_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="RedturtlePrenotazioniRestApiLayer:Integration",
)

REDTURTLE_PRENOTAZIONI_API_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_PRENOTAZIONI_API_FIXTURE, z2.ZSERVER_FIXTURE),
    name="RedturtlePrenotazioniRestApiLayer:Functional",
)

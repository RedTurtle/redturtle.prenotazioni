# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import redturtle.prenotazioni


class RedturtlePrenotazioniLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.prenotazioni)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'redturtle.prenotazioni:default')


REDTURTLE_PRENOTAZIONI_FIXTURE = RedturtlePrenotazioniLayer()


REDTURTLE_PRENOTAZIONI_INTEGRATION_TESTING = IntegrationTesting(
    bases=(REDTURTLE_PRENOTAZIONI_FIXTURE,),
    name='RedturtlePrenotazioniLayer:IntegrationTesting',
)


REDTURTLE_PRENOTAZIONI_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_PRENOTAZIONI_FIXTURE,),
    name='RedturtlePrenotazioniLayer:FunctionalTesting',
)


REDTURTLE_PRENOTAZIONI_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        REDTURTLE_PRENOTAZIONI_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='RedturtlePrenotazioniLayer:AcceptanceTesting',
)

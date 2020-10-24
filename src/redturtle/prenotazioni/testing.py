# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import collective.contentrules.mailfromfield
import collective.z3cform.datagridfield
import plone.restapi
import redturtle.prenotazioni


class RedturtlePrenotazioniLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.prenotazioni)
        self.loadZCML(package=collective.contentrules.mailfromfield)
        self.loadZCML(package=collective.z3cform.datagridfield)

    def setUpPloneSite(self, portal):
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

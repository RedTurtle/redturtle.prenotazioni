# -*- coding: utf-8 -*-
from zope.component import queryUtility
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.workflow.remap import remap_workflow
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.app.contentrules.conditions.wfstate import WorkflowStateCondition
from plone.app.contentrules.conditions.wftransition import WorkflowTransitionCondition
from plone import api

import logging

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = "profile-redturtle.prenotazioni:default"


def update_profile(context, profile):
    context.runImportStepFromProfile(DEFAULT_PROFILE, profile)


def update_registry(context):
    update_profile(context, "plone.app.registry")


def update_actions(context):
    update_profile(context, "actions")


def update_catalog(context):
    update_profile(context, "catalog")


def update_controlpanel(context):
    update_profile(context, "controlpanel")


def update_types(context):
    update_profile(context, "typeinfo")


def update_rolemap(context):
    update_profile(context, "rolemap")


def update_contentrules(context):
    update_profile(context, "contentrules")


def reload_gs_profile(context):
    loadMigrationProfile(
        context,
        DEFAULT_PROFILE,
    )


def to_1001(context):
    update_rolemap(context)
    update_actions(context)


def to_1002(context):
    update_registry(context)


def to_1100(context):

    brains = api.content.find(portal_type="Prenotazione")
    tot = len(brains)

    logger.info("Remapping fields")

    i = 0
    for brain in brains:
        i += 1
        obj = brain.getObject()
        if i % 100 == 0:
            logger.info("%s/%s" % (i, tot))
        tipologia_prenotazione = getattr(obj, "tipologia_prenotazione", None)
        data_prenotazione = getattr(obj, "data_prenotazione", None)
        azienda = getattr(obj, "azienda", None)
        data_scadenza = getattr(obj, "data_scadenza", None)

        if tipologia_prenotazione:
            obj.booking_type = tipologia_prenotazione
            obj.tipologia_prenotazione = None

        if data_prenotazione:
            obj.booking_date = data_prenotazione
            obj.data_prenotazione = None

        if azienda:
            obj.company = azienda
            obj.azienda = None

        if data_scadenza:
            obj.booking_expiration_date = data_scadenza
            obj.data_scadenza = None


def to_1400(context):
    """Upgrade the prenotazioni_workflow"""
    update_profile(context, "workflow")
    update_contentrules(context)

    workflow_state_map = {
        "published": "confirmed",
        "private": "private",
        "pending": "pending",
        "refused": "refused",
    }

    # if we find the exception the code must fail
    remap_workflow(
        context, ("Prenotazione",), ("prenotazioni_workflow",), workflow_state_map
    )

    rule_storage = queryUtility(IRuleStorage)

    for rule in rule_storage.items():
        rule = rule[1]

        if "Prenotazione" in getattr(
            rule.conditions and rule.conditions[0], "check_types", []
        ):
            if len(rule.conditions) > 1:
                if isinstance(
                    rule.conditions[1],
                    WorkflowTransitionCondition,
                ):
                    wf_states = list(rule.conditions[1].wf_transitions)

                    if "publish" in wf_states:
                        wf_states.remove("publish")
                        wf_states.append("confirm")

                        rule.conditions[1].wf_transitions = set(wf_states)

                if isinstance(
                    rule.conditions[1],
                    WorkflowStateCondition,
                ):
                    wf_states = list(rule.conditions[1].wf_states)

                    if "publish" in wf_states:
                        wf_states.remove("published")
                        wf_states.append("confirmed")

                        rule.conditions[1].wf_states = set(wf_states)

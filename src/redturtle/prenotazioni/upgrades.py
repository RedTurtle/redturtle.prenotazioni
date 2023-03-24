# -*- coding: utf-8 -*-
from plone import api
from plone.app.contentrules.actions.workflow import WorkflowAction
from plone.app.contentrules.conditions.portaltype import PortalTypeCondition
from plone.app.contentrules.conditions.wfstate import WorkflowStateCondition
from plone.app.contentrules.conditions.wftransition import WorkflowTransitionCondition
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.workflow.remap import remap_workflow
from plone.contentrules.engine.interfaces import IRuleStorage
from zope.component import queryUtility

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
        # handle case of the upgrade step double run
        "confirmed": "confirmed",
    }

    # if we find the exception the code must fail
    remap_workflow(
        context, ("Prenotazione",), ("prenotazioni_workflow",), workflow_state_map
    )

    rule_storage = queryUtility(IRuleStorage)

    for rule in rule_storage.items():
        rule = rule[1]

        portal_type_conditions = filter(
            lambda item: isinstance(item, PortalTypeCondition), rule.conditions
        )

        workflow_state_conditions = filter(
            lambda item: isinstance(item, WorkflowStateCondition), rule.conditions
        )

        workflow_transition_conditions = filter(
            lambda item: isinstance(item, WorkflowTransitionCondition), rule.conditions
        )

        for portal_type_condition in portal_type_conditions:
            if "Prenotazione" in getattr(portal_type_condition, "check_types", []):
                for workflow_transition_condition in workflow_transition_conditions:
                    if isinstance(
                        workflow_transition_condition, WorkflowTransitionCondition
                    ):
                        wf_states = list(workflow_transition_condition.wf_transitions)

                        if "publish" in wf_states:
                            wf_states.remove("publish")
                            wf_states.append("confirm")

                            workflow_transition_condition.wf_transitions = set(
                                wf_states
                            )

                for workflow_state_condition in workflow_state_conditions:
                    if isinstance(workflow_state_condition, WorkflowStateCondition):
                        wf_states = list(workflow_state_condition.wf_states)

                        if "publish" in wf_states:
                            wf_states.remove("published")
                            wf_states.append("confirmed")

                            workflow_state_condition.wf_states = set(wf_states)


def to_1401(context):
    update_types(context)

    rule_storage = queryUtility(IRuleStorage)
    for rule in rule_storage.items():
        rule = rule[1]

        workflow_action_conditions = filter(
            lambda item: isinstance(item, WorkflowAction), rule.actions
        )
        portal_type_conditions = filter(
            lambda item: isinstance(item, PortalTypeCondition), rule.conditions
        )

        if [
            condition
            for condition in portal_type_conditions
            if "Prenotazione" in getattr(condition, "check_types", [])
        ]:
            for workflow_action in workflow_action_conditions:
                if workflow_action.transition == "publish":
                    workflow_action.transition = "confirm"

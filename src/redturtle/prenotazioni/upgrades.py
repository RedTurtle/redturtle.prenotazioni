# -*- coding: utf-8 -*-
from plone import api
from plone.app.contentrules.actions.workflow import WorkflowAction
from plone.app.contentrules.conditions.portaltype import PortalTypeCondition
from plone.app.contentrules.conditions.wfstate import WorkflowStateCondition
from plone.app.contentrules.conditions.wftransition import (
    WorkflowTransitionCondition,
)
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.workflow.remap import remap_workflow
from plone.contentrules.engine.interfaces import IRuleStorage
from zope.component import queryUtility
from zope.component import getUtility

import logging


logger = logging.getLogger(__name__)

DEFAULT_PROFILE = "profile-redturtle.prenotazioni:default"
CONTENT_RULES_EVOLUTION_PROFILE = (
    "profile-redturtle.prenotazioni:content_rules_evolution"
)


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
        context,
        ("Prenotazione",),
        ("prenotazioni_workflow",),
        workflow_state_map,
    )

    rule_storage = queryUtility(IRuleStorage)

    for rule in rule_storage.items():
        rule = rule[1]

        portal_type_conditions = filter(
            lambda item: isinstance(item, PortalTypeCondition), rule.conditions
        )

        workflow_state_conditions = filter(
            lambda item: isinstance(item, WorkflowStateCondition),
            rule.conditions,
        )

        workflow_transition_conditions = filter(
            lambda item: isinstance(item, WorkflowTransitionCondition),
            rule.conditions,
        )

        for portal_type_condition in portal_type_conditions:
            if "Prenotazione" in getattr(
                portal_type_condition, "check_types", []
            ):
                for (
                    workflow_transition_condition
                ) in workflow_transition_conditions:
                    if isinstance(
                        workflow_transition_condition,
                        WorkflowTransitionCondition,
                    ):
                        wf_states = list(
                            workflow_transition_condition.wf_transitions
                        )

                        if "publish" in wf_states:
                            wf_states.remove("publish")
                            wf_states.append("confirm")

                            workflow_transition_condition.wf_transitions = set(
                                wf_states
                            )

                for workflow_state_condition in workflow_state_conditions:
                    if isinstance(
                        workflow_state_condition, WorkflowStateCondition
                    ):
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


def to_1402(context):
    # load new content rules
    context.runImportStepFromProfile(
        CONTENT_RULES_EVOLUTION_PROFILE, "contentrules"
    )


def to_1403(context):
    update_catalog(context)

    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="Prenotazione"
    ):
        brain.getObject().reindexObject(idxs=["fiscalcode"])


def to_1500(context):
    context.runImportStepFromProfile(
        "profile-redturtle.prenotazioni:to_1500", "typeinfo"
    )


def to_1502_upgrade_texts(context):
    from plone.app.textfield.value import RichTextValue

    instructions_default = (
        "I testi e l’oggetto delle notifiche email possono essere configurate usando le seguenti variabili:"
        "<ul>"
        "<li>${title} - Titolo della prenotazione.</li>"
        "<li>${booking_gate} - Sportello della prenotazione.</li>"
        "<li>${booking_human_readable_start} - Data e ora prenotazione con formattazione standard.</li>"
        "<li>${booking_date} - Data prenotazione.</li>"
        "<li>${booking_end_date} - Data fine prenotazione.</li>"
        "<li>${booking_time} - Orario di inizio prenotazione.</li>"
        "<li>${booking_time_end} - Orario di fine prenotazione.</li>"
        "<li>${booking_code} - Ticket identificativo della prenotazione da utilizzare per chiamare il cittadino allo sportello ad attesa ultimata.</li>"
        "<li>${booking_type} - Tipologia prenotazione.</li>"
        "<li>${booking_print_url} - Link di riepilogo prenotazione.</li>"
        "<li>${booking_url_with_delete_token} - Link per cancellare la prenotazione.</li>"
        "<li>${booking_user_phone} - Numero di telefono del cittadino.</li>"
        "<li>${booking_user_email} - Email del cittadino.</li>"
        "<li>${booking_office_contact_phone} - Telefono ufficio, se compilato.</li>"
        "<li>${booking_office_contact_pec} - PEC ufficio, se compilata.</li>"
        "<li>${booking_office_contact_fax} - Fax ufficio, se compilato.</li>"
        "<li>${booking_how_to_get_to_office} - Informazioni su come raggiungere l’ufficio, se compilate.</li>"
        "<li>${booking_office_complete_address} - Indirizzo completo dell’ufficio, se compilato.</li>"
        "</ul>"
    )
    new_fields = {
        "notify_on_submit_subject": "Prenotazione creata correttamente per ${title}",
        "notify_on_submit_message": "notify_on_submit_message",
        "notify_on_confirm_subject": "Prenotazione del ${booking_date} alle ${booking_time} accettata",
        "notify_on_confirm_message": (
            "La prenotazione ${booking_type} per ${title} è stata confermata!"
            "Se non hai salvato o stampato il promemoria, puoi visualizzarlo su <a href=${booking_print_url}>questo link</a>"
            "Se desideri cancellare la prenotazione, accedi a <a href=${booking_print_url}>questo link</a>"
        ),
        "notify_on_move_subject": (
            "Modifica data di prenotazione per ${title}"
        ),
        "notify_on_move_message": (
            "L'orario della sua prenotazione ${booking_type} è stata modificato."
            "La nuova data è ${booking_date} alle ore ${booking_time}."
            "Controlla o stampa il nuovo promemoria su  <a href=${booking_print_url}>questo link</a>."
        ),
        "notify_on_refuse_subject": "Prenotazione rifiutata per ${title}",
        "notify_on_refuse_message": "La prenotazione ${booking_type} del ${booking_date} delle ore ${booking_time} è stata rifiutata.",
    }

    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        object = brain.getObject()

        logger.info(f"[1501-1502] Updating fields on {brain.getPath()}")

        object.templates_usage = RichTextValue(
            instructions_default, "text/html", "text/html"
        )

        for name, value in new_fields.items():
            setattr(object, name, value)


def to_1502_upgrade_contentrules(context):
    from plone.contentrules.engine.interfaces import IRuleStorage

    rules_to_delete = [
        "booking-accepted",
        "booking-moved",
        "booking-created-user",
        "booking-refuse",
        "booking-confirm",
    ]

    rule_storage = getUtility(IRuleStorage)

    for rule in rules_to_delete:
        if rule_storage.get(rule):
            # It is supposed that all the rule assignments will be deleted by plone.app.contentrules
            # event handlers which are supposed to do that
            logger.info(f"[1501-1502] Deleting contentrule `{rule}`")
            del rule_storage[rule]

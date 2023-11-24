# -*- coding: utf-8 -*-
import logging

import pytz
from plone import api
from plone.app.contentrules.actions.workflow import WorkflowAction
from plone.app.contentrules.conditions.portaltype import PortalTypeCondition
from plone.app.contentrules.conditions.wfstate import WorkflowStateCondition
from plone.app.contentrules.conditions.wftransition import WorkflowTransitionCondition
from plone.app.event.base import default_timezone
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.workflow.remap import remap_workflow
from plone.contentrules.engine.interfaces import IRuleStorage
from zope.component import getUtility
from zope.component import queryUtility

from redturtle.prenotazioni import _
from redturtle.prenotazioni.events.prenotazione import set_booking_code

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


def update_sharing(context):
    update_profile(context, "sharing")


def update_workflow(context):
    update_profile(context, "workflow")


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
            if "Prenotazione" in getattr(portal_type_condition, "check_types", []):
                for workflow_transition_condition in workflow_transition_conditions:
                    if isinstance(
                        workflow_transition_condition,
                        WorkflowTransitionCondition,
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


def to_1402(context):
    # load new content rules
    context.runImportStepFromProfile(CONTENT_RULES_EVOLUTION_PROFILE, "contentrules")


def to_1403(context):
    update_catalog(context)

    for brain in api.portal.get_tool("portal_catalog")(portal_type="Prenotazione"):
        brain.getObject().reindexObject(idxs=["fiscalcode"])


def to_1500(context):
    context.runImportStepFromProfile(
        "profile-redturtle.prenotazioni:to_1500", "typeinfo"
    )


def to_1502(context):
    update_catalog(context)

    for brain in api.portal.get_tool("portal_catalog")(portal_type="Prenotazione"):
        logger.info(f"[ 1500 - 1501 ] - Rindexing <{brain.getPath()}>")
        brain.getObject().reindexObject(idxs=["booking_type"])


def to_1600_popolate_templates(context):
    notify_on_submit_subject = context.translate(
        _("notify_on_submit_subject_default_value", "Booking created ${title}")
    )

    notify_on_submit_message = context.translate(
        _(
            "notify_on_submit_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} was created.<a href=${booking_print_url}>Link</a>",
        )
    )

    notify_on_confirm_subject = context.translate(
        _(
            "notify_on_confirm_subject_default_value",
            "Booking of ${booking_date} at ${booking_time} was accepted",
        )
    )

    notify_on_confirm_message = context.translate(
        _(
            "notify_on_confirm_message_default_value",
            "The booking${booking_type} for ${title} was confirmed! <a href=${booking_print_url}>Link</a>",
        )
    )

    notify_on_move_subject = context.translate(
        _(
            "notify_on_move_subject_default_value",
            "Modified the boolking date for ${title}",
        )
    )

    notify_on_move_message = context.translate(
        _(
            "notify_on_move_message_default_value",
            "The booking scheduling of ${booking_type} was modified."
            "The new one is on ${booking_date} at ${booking_time}. <a href=${booking_print_url}>Link</a>.",
        )
    )

    notify_on_refuse_subject = context.translate(
        _(
            "notify_on_refuse_subject_default_value",
            "Booking refused for ${title}",
        )
    )

    notify_on_refuse_message = context.translate(
        _(
            "notify_on_refuse_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )

    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        obj = brain.getObject()
        obj.notify_on_submit_subject = notify_on_submit_subject
        obj.notify_on_submit_message = notify_on_submit_message
        obj.notify_on_confirm_subject = notify_on_confirm_subject
        obj.notify_on_confirm_message = notify_on_confirm_message
        obj.notify_on_move_subject = notify_on_move_subject
        obj.notify_on_move_message = notify_on_move_message
        obj.notify_on_refuse_subject = notify_on_refuse_subject
        obj.notify_on_refuse_message = notify_on_refuse_message


def to_1600_upgrade_contentrules(context):
    from plone.contentrules.engine.interfaces import IRuleAssignmentManager
    from plone.contentrules.engine.interfaces import IRuleStorage

    rules_to_delete = [
        "booking-accepted",
        "booking-moved",
        "booking-created-user",
        "booking-refuse",
        "booking-confirm",
    ]

    rule_storage = getUtility(IRuleStorage)

    for brain in api.portal.get_tool("portal_catalog")(
        portal_type=["PrenotazioniFolder", "Plone Site", "Folder"]
    ):
        obj = brain.getObject()
        assignable = IRuleAssignmentManager(obj, None)
        contentrules_mapping = {
            "booking-accepted": "notify_on_confirm",
            "booking-moved": "notify_on_move",
            "booking-refuse": "notify_on_reject",
            "booking-created-user": "notify_on_submit",
        }

        for old, new in contentrules_mapping.items():
            if assignable.get("booking-confirm", None):
                setattr(obj, "notify_on_confirm", True)
                setattr(obj, "auto_confirm", True)

                if new == "notify_on_submit":
                    continue

            if assignable.get(old, None):
                setattr(obj, new, True)

    for rule in rules_to_delete:
        if rule_storage.get(rule):
            # It is supposed that all the rule assignments will be deleted by plone.app.contentrules
            # event handlers which are supposed to do that
            logger.info(f"[1501-1502] Deleting contentrule `{rule}`")
            del rule_storage[rule]

    update_contentrules(context)


def to_1601(context):
    for brain in api.portal.get_tool("portal_catalog")(portal_type="Prenotazione"):
        brain.getObject().reindexObject(idxs=["SearchableText"])


def to_1700(context):
    """
    Fix timezones in bookings
    """
    from dateutil.tz.tz import tzutc

    brains = api.content.find(portal_type="Prenotazione")
    tot = len(brains)
    i = 0
    for brain in brains:
        i += 1
        if i % 100 == 0:
            logger.info("Progress: {}/{}".format(i, tot))
        prenotazione = brain.getObject()

        fields = ["booking_date", "booking_expiration_date"]
        for field in fields:
            date = getattr(prenotazione, field, None)
            if date.tzinfo is None or isinstance(date.tzinfo, tzutc):
                # set current timezone
                tz = pytz.timezone(default_timezone())
                setattr(prenotazione, field, date.astimezone(tz))


def to_1800(context):
    brains = api.content.find(portal_type="PrenotazioniFolder")
    for brain in brains:
        item = brain.getObject()
        same_day_booking_disallowed = getattr(item, "same_day_booking_disallowed", None)
        if same_day_booking_disallowed not in ("yes", "no"):
            item.same_day_booking_disallowed = "no"
            logger.info(
                f'- [{brain.getPath()}] set same_day_booking_disallowed to "no"'
            )


def update_booking_code(context):
    brains = api.content.find(portal_type="Prenotazione")
    for brain in brains:
        item = brain.getObject()
        if not getattr(item, "booking_code", None):
            set_booking_code(item, None)
            item.reindexObject(idxs=["SearchableText"])
            logger.info(
                f"- [{brain.getPath()}] set booking_code to {item.booking_code}"
            )


def to_1804(context):
    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        logger.info("Updating <{UID}>.max_bookings_allowed=2".format(UID=brain.UID))
        brain.getObject().max_bookings_allowed = 2


def to_1805(context):
    from plone.app.textfield.value import RichTextValue

    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        obj = brain.getObject()

        if obj.cosa_serve and type(obj.cosa_serve) is not RichTextValue:
            obj.cosa_serve = RichTextValue(
                raw=obj.cosa_serve,
                mimeType="text/html",
                outputMimeType="text/html",
                encoding="utf-8",
            )
            logger.info(
                "Converted <{UID}>.cosa_serve to RichText".format(UID=brain.UID)
            )


def to_1806(context):
    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        logger.info("Updating the <{UID}>.booking_types".format(UID=brain.UID))

        for type in getattr(brain.getObject(), "booking_types", []):
            if "hidden" not in type.keys():
                type["hidden"] = False


def to_1807(context):
    for brain in api.portal.get_tool("portal_catalog")(
        portal_type="PrenotazioniFolder"
    ):
        obj = brain.getObject()
        if obj.notify_on_refuse_message:
            obj.notify_on_refuse_message += (
                " Motivo del rifiuto: ${booking_refuse_message}"
            )

        logger.info(
            "Upgraded <{UID}>.notify_on_refuse_message value".format(UID=brain.UID)
        )


def to_1808(context):
    api.portal.get_tool("portal_workflow").updateRoleMappings()

    for brain in api.content.find(portal_type="Prenotazione"):
        brain.getObject().reindexObjectSecurity()
        logger.info("Upgraded <{UID}> security settings".format(UID=brain.UID))


def to_2000(context):
    for brain in api.content.find(portal_type="PrenotazioniFolder"):
        obj = brain.getObject()
        booking_types = obj.__dict__.get("booking_types", [])
        if not booking_types:
            continue
        logger.info(
            f"Transforming <{brain.UID}>.booking_types to contenttypes themself"
        )
        for booking_type in booking_types:
            logger.info(f" --| Creating {booking_type.get('name')} booking type")
            booking_type_obj = api.content.create(
                type="PrenotazioneType",
                title=booking_type.get("name"),
                duration=booking_type.get("duration"),
                container=obj,
            )
            if not booking_type.get("hidden", False):
                api.content.transition(obj=booking_type_obj, transition="publish")
            booking_type_obj.reindexObject(idxs=["review_state"])

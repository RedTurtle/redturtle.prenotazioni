# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
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


def reload_gs_profile(context):
    loadMigrationProfile(
        context, DEFAULT_PROFILE,
    )


def to_1001(context):
    update_rolemap(context)
    update_actions(context)


def to_1002(context):
    update_registry(context)

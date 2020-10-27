# -*- coding: utf-8 -*-
from plone.app.contentrules.rule import get_assignments
from plone.contentrules.engine.assignments import RuleAssignment
from plone.contentrules.engine.interfaces import IRuleAssignmentManager
from plone.contentrules.engine.interfaces import IRuleStorage
from zope.component import getUtility


def on_create(obj, event):
    """
    temporary disabled
    """
    storage = getUtility(IRuleStorage)
    assignable = IRuleAssignmentManager(obj)
    for rule_id in [
        "booking-accepted",
        "booking-moved",
        "booking-created-user",
        "booking-refuse",
    ]:

        assignable[rule_id] = RuleAssignment(rule_id)
        assignable[rule_id].bubbles = True
        get_assignments(storage[rule_id]).insert(
            "/".join(obj.getPhysicalPath())
        )

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


def sort_on_creation_or_change(obj, event):
    """
    There is no way yet to sort correctly pause on prenotazioni folder using
    datagrid widget. I prefer to reorder the rows to have a more readable table
    """
    pauses = obj.pause_table[:]
    pauses.sort(key=lambda x: (x["day"], x["pause_start"]))
    obj.pause_table = pauses

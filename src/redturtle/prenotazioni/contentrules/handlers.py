# -*- coding: utf-8 -*-
from plone.app.contentrules.handlers import execute_rules


def moved(event):
    """
    When a booking is moved, execute the rules assigned to his parent.
    """
    execute_rules(event)

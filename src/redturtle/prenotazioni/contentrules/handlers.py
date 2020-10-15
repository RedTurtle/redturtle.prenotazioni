try:
    from plone.app.contentrules.handlers import execute_rules
except ImportError:
    # Plone 3.3
    from Acquisition import aq_inner
    from Acquisition import aq_parent
    from plone.app.contentrules.handlers import execute
    from plone.app.contentrules.handlers import is_portal_factory

    def execute_rules(event):
        """ When an action is invoked on an object,
            execute rules assigned to its parent.
            Base action executor handler """
        if is_portal_factory(event.object):
            return

        execute(aq_parent(aq_inner(event.object)), event)


def moved(event):
    """
    When a booking is moved, execute the rules assigned to his parent.
    """
    execute_rules(event)

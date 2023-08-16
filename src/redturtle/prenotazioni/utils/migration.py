from zope.globalrequest import getRequest
from collective.exportimport.interfaces import IMigrationMarker


def is_migration():
    """Returns True if the current reqeust provides the migration marker"""
    return IMigrationMarker.providedBy(getRequest())

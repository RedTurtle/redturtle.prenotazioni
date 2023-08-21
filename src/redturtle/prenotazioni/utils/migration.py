# -*- coding: utf-8 -*-
from zope.globalrequest import getRequest

try:
    from collective.exportimport.interfaces import IMigrationMarker
except ImportError:
    IMigrationMarker = None


def is_migration():
    """Returns True if the current reqeust provides the migration marker"""
    return IMigrationMarker and IMigrationMarker.providedBy(getRequest())

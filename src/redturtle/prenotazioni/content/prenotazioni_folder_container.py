# -*- coding: utf-8 -*-
from plone.app.contenttypes.content import Folder
from plone.app.contenttypes.interfaces import IFolder
from zope.interface import implementer


@implementer(IFolder)
class PrenotazioniFolderContainer(Folder):
    @property
    def exclude_from_nav(self):
        return True

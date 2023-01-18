from zope.interface import implementer
from plone.app.contenttypes.interfaces import IFolder
from plone.app.contenttypes.content import Folder


@implementer(IFolder)
class PrenotazioniFolderContainer(Folder):
    @property
    def exclude_from_nav(self):
        return False

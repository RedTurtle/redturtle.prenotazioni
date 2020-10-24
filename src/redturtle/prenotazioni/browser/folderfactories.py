# -*- coding: utf-8 -*-
from plone.app.content.browser.folderfactories import (
    FolderFactoriesView as BaseView,
)


class FolderFactoriesView(BaseView):

    """The folder_factories view - show addable types
    """

    hidden_types = ("Prenotazione",)

    def addable_types(self, include=None):
        """Return menu item entries in a TAL-friendly form.

        Pass a list of type ids to 'include' to explicitly allow a list of
        types.
        """
        addable_types = super(FolderFactoriesView, self).addable_types(include)
        addable_types = [
            x for x in addable_types if x.get("id") not in self.hidden_types
        ]
        return addable_types

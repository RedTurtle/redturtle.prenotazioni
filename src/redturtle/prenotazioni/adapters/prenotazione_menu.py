# -*- coding: utf-8 -*-
from plone.app.contentmenu.menu import ActionsSubMenuItem
from plone.memoize.view import memoize


class PrenotazioneActionsSubMenuItem(ActionsSubMenuItem):

    @memoize
    def available(self):
        ''' Never available :)
        '''
        return True

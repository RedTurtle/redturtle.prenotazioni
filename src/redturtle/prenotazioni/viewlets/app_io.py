# -*- encoding: utf-8 -*-
from plone.app.layout.viewlets.common import ViewletBase
from redturtle.prenotazioni.config import NOTIFICATIONS_LOGS
from zope.annotation.interfaces import IAnnotations


class Viewlet(ViewletBase):
    def available(self):
        return getattr(self.context, "app_io_enabled", False)

    def logs(self):
        annotations = IAnnotations(self.context)
        return [v for (k, v) in annotations.items() if k.startswith(NOTIFICATIONS_LOGS)]

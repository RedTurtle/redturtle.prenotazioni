# -*- coding: utf-8 -*-
from plone.indexer.decorator import indexer
from Products.CMFPlone.utils import safe_unicode
from redturtle.prenotazioni.content.prenotazione import IPrenotazione


@indexer(IPrenotazione)
def SearchableText_prenotazione(obj):
    if obj.subject:
        subject = " ".join([safe_unicode(s) for s in obj.subject])
    else:
        subject = ""

    return " ".join(
        (
            safe_unicode(obj.id),
            safe_unicode(obj.title) or "",
            safe_unicode(obj.description) or "",
            safe_unicode(obj.email or ""),
            safe_unicode(obj.phone or ""),
            safe_unicode(obj.booking_type or ""),
            safe_unicode(obj.company or ""),
            safe_unicode(obj.gate or ""),
            safe_unicode(obj.staff_notes or ""),
            subject,
        )
    )


@indexer(IPrenotazione)
def Subject_prenotazione(obj):
    subject = list(obj.subject)
    subject.append("Gate: {}".format(getattr(obj, "gate", "")))
    return sorted(subject)


@indexer(IPrenotazione)
def Date(obj):
    """
    Set as booking_date
    """
    return obj.Date()

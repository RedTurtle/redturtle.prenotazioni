# -*- coding: utf-8 -*-
from plone.indexer.decorator import indexer

from redturtle.prenotazioni.content.prenotazione import IPrenotazione

try:
    from plone.base.utils import safe_text
except ImportError:
    # Plone < 6
    from Products.CMFPlone.utils import safe_unicode as safe_text


@indexer(IPrenotazione)
def SearchableText_prenotazione(obj):
    if obj.subject:
        subject = " ".join([safe_text(s) for s in obj.subject])
    else:
        subject = ""

    return " ".join(
        (
            safe_text(obj.id),
            safe_text(obj.title) or "",
            safe_text(obj.description) or "",
            safe_text(obj.email or ""),
            safe_text(obj.phone or ""),
            safe_text(obj.booking_type or ""),
            safe_text(obj.company or ""),
            safe_text(obj.gate or ""),
            safe_text(obj.staff_notes or ""),
            safe_text(obj.getBookingCode() or ""),
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


@indexer(IPrenotazione)
def fiscalcode(obj):
    """upper-ize fiscalcode for case insensitive search"""
    if obj.fiscalcode:
        return obj.fiscalcode.upper()

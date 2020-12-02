# -*- coding: utf-8 -*-
from plone import api
from time import time
from json import dumps


def log_data_for_booking(obj, data):
    """ Log the given data for a booking
    """
    prenotazioni_folder = obj.getPrenotazioniFolder()
    user = api.user.get_current()
    booking_stats = api.content.get_view(
        "booking_stats", prenotazioni_folder, prenotazioni_folder.REQUEST
    )
    data.extend(
        [
            time(),
            prenotazioni_folder.UID(),
            obj.UID(),
            obj.Title(),
            user.getId() or "anonymous",
        ]
    )
    booking_stats.csvlog(data)


def on_workflow_change(obj, event):
    """
    This handler logs a cvs string for
    each IPrenotazione workflow changes
    """
    data = [event.action, ""]
    log_data_for_booking(obj, data)


def on_move(obj, event):
    """
    This handler logs a cvs string for
    every IPrenotazione document moved
    """
    data = ["moved", ""]
    log_data_for_booking(obj, data)


def on_modify(obj, event):
    """
    This handler logs a cvs string for
    every IPrenotazione document modified
    """
    old_version = getattr(obj, "version_id", 0) - 1
    if old_version < 0:
        return

    # Below a list of fields to be logged to
    fnames = [
        "azienda",
        "description",
        "email",
        "gate",
        "phone",
        "staff_notes",
        "tipologia_prenotazione",
        "title",
    ]
    pr = api.portal.get_tool(name="portal_repository")
    old = pr.retrieve(obj, old_version).object
    changes = []
    for fname in fnames:
        c_value = obj.getField(fname, obj).get(obj)
        o_value = old.getField(fname, old).get(old)
        if c_value != o_value:
            changes.append({"new_" + fname: c_value, "old_" + fname: o_value})

    data = ["changed", dumps(changes)]
    log_data_for_booking(obj, data)

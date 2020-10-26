# -*- coding: utf-8 -*-
from datetime import timedelta
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from redturtle.prenotazioni.adapters.slot import BaseSlot
from six.moves import range
from zope.component import Interface
from zope.interface import implementer

import six


class IConflictManager(Interface):
    """
    Interface for a booker
    """


@implementer(IConflictManager)
class ConflictManager(object):
    portal_type = "Prenotazione"
    # We consider only those state as active. I.e.: prenotazioni rejected are
    # not counted!
    active_review_state = ["published", "pending"]

    def __init__(self, context):
        """
        @param context: a PrenotazioniFolder object
        """
        self.context = context

    @property
    @memoize
    def prenotazioni(self):
        """ The prenotazioni context state view
        """
        return self.context.restrictedTraverse("@@prenotazioni_context_state")

    @property
    @memoize
    def base_query(self):
        """
        A query that returns objects in this context
        """
        return {
            "portal_type": self.portal_type,
            "path": "/".join(self.context.getPhysicalPath()),
        }

    def get_limit(self):
        """
        Get's the limit for concurrent objects
        It is given by the number of active gates (if specified)
        or defaults to one
        There is also a field that disables gates, we should remove them from
        this calculation
        """
        if not self.prenotazioni.get_gates():
            return 1
        return len(self.prenotazioni.get_available_gates())

    def unrestricted_prenotazioni(self, **kw):
        """
        Query our prenotazioni
        """
        query = self.base_query.copy()
        query.update(kw)
        pc = getToolByName(self.context, "portal_catalog")
        brains = pc.unrestrictedSearchResults(**query)
        return brains

    def search_bookings_by_date_range(self, start, stop, **kw):
        """
        Query our prenotazioni
        """
        query = kw.copy()
        query["Date"] = {"query": [start, stop], "range": "min:max"}
        return self.unrestricted_prenotazioni(**query)

    def get_choosen_slot(self, data):
        """ Get's the slot requested by the user
        """
        tipology = data.get("tipology", "")
        tipology_duration = self.prenotazioni.get_tipology_duration(tipology)
        start = data.get("booking_date", "")
        end = start + timedelta(seconds=tipology_duration * 60)
        slot = BaseSlot(start, end)
        return slot

    def extend_availability(self, slots, gate_slots):
        """ We add slots to the gate_slots list and we make unions
        when they overlap.
        """
        for i in range(len(gate_slots)):
            for slot in slots:
                if gate_slots[i].overlaps(slot):
                    interval = gate_slots[i].union(slot)
                    gate_slots[i] = BaseSlot(
                        interval.lower_value, interval.upper_value
                    )

        return gate_slots + slots

    def add_exclude(self, exclude, availability):
        """ Extends the availability list adding the slot we are moving
        """
        for key in six.iterkeys(exclude):
            if availability.get(key, None):
                availability[key] = self.extend_availability(
                    exclude[key], availability[key]
                )

        return availability

    def conflicts(self, data, exclude=None):
        """
        Check if we already have a conflictual booking

        :param exclude: exclude a time slot (useful when we want to move
                        something).
                        Exclude should be a dict in the form
                        {'gate1' : [slot11, slot12, ...],
                         'gate2' : [slot21, slot22, ...],
                        }
        """
        booking_date = data.get("booking_date", "")
        slot = self.get_choosen_slot(data)
        availability = self.prenotazioni.get_free_slots(booking_date)

        if exclude:
            availability = self.add_exclude(exclude, availability)

        for gate_slots in six.itervalues(availability):
            for gate_slot in gate_slots:
                if slot in gate_slot:
                    return False
        return True

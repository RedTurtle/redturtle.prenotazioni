# -*- coding: utf-8 -*-
from redturtle.prenotazioni.content.prenotazione import IPrenotazione
from zope.component import adapter
from zope.component import Interface
from zope.interface import implementer

import hashlib


class IBookingCodeGenerator(Interface):
    """
    Adapter interface to generate a code
    """


@implementer(IBookingCodeGenerator)
@adapter(IPrenotazione, Interface)
class BookingCodeGenerator:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, *args, **kwargs):
        hash_obj = hashlib.blake2b(
            bytes(self.context.UID(), encoding="utf8"), digest_size=3
        )

        return hash_obj.hexdigest().upper()

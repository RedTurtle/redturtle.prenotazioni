from zope.interface import implementer
from zope.publisher.interfaces import IRequest
from zope.component import adapter
from plone.restapi.interfaces import ISerializeToJson

from redturtle.prenotazioni.adapters.slot import ISlot
from redturtle.prenotazioni.interfaces import IRedturtlePrenotazioniLayer


@implementer(ISerializeToJson)
@adapter(ISlot, IRequest)
class SlotSerializer:
    def __init__(self, context, request):
        self.context = context
        self.reqeuest = request

    def __call__(self, *args, **kwargs):
        return {"start": self.context.start(), "stop": self.context.stop()}

from asphalt.core import Event, Signal
from meshage.messages import MeshtasticMessage


class ReceivedMessageEvent(Event):
    def __init__(self, source, topic, message: MeshtasticMessage):
        super().__init__(source, topic)
        self.message = message


class ReceivedMessageEventSource:
    signal = Signal(ReceivedMessageEvent)

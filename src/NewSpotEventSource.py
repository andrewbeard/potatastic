from asphalt.core import Event, Signal

from .Spot import Spot


class NewSpotEvent(Event):
    def __init__(self, source, topic, spot: Spot):
        super().__init__(source, topic)
        self.spot = spot


class NewSpotEventSource:
    signal = Signal(NewSpotEvent)

from asphalt.core import Event, Signal


class CommandEvent(Event):
    def __init__(self, source, topic, command: str, userId: int):
        super().__init__(source, topic)
        self.command = command
        self.userId = userId


class CommandEventSource:
    signal = Signal(CommandEvent)

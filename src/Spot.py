from datetime import datetime
from typing import Any


class Spot:
    def __init__(self, spot: dict[str, Any]):
        self.callsign = spot["activator"]
        self.frequency = float(spot["frequency"])
        self.grid = spot["grid4"]
        self.mode = spot["mode"]
        self.name = spot["name"]
        self.reference = spot["reference"]
        self.id = spot["spotId"]
        self.spotter = spot["spotter"]
        self.timestamp = datetime.fromisoformat(spot["spotTime"])

    def __str__(self):
        return f"{self.callsign} @ {self.frequency} {self.mode}\n{self.reference} ({self.name})"

    @property
    def key(self) -> str:
        return f"{self.callsign}-{self.frequency}-{self.mode}"

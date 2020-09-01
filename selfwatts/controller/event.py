from typing import List
from datetime import datetime


class ControlEvent:
    """
    Control Event class.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, action: str, parameters: List[str]) -> None:
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target
        self.action = action
        self.parameters = parameters

    def __repr__(self):
        return 'ControlEvent({}, {}, {}, {}, {})'.format(self.timestamp, self.sensor, self.target, self.action, self.parameters)


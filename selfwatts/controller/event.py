from typing import List
from datetime import datetime


class ControlEvent:
    """
    Control Event class.
    """

    def __init__(self, timestamp: datetime, hostname: str, events: List[str]) -> None:
        self.timestamp = timestamp
        self.hostname = hostname
        self.events = events

    def __repr__(self):
        return 'ControlEvent({}, {}, {})'.format(self.timestamp, self.hostname, self.events)


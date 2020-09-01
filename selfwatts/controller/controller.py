import logging
from typing import List
from random import shuffle

from selfwatts.controller.database import DatabaseAdapter
from selfwatts.controller.invoker import HwpcSensorInvoker
from selfwatts.controller.libpfm_wrapper import get_available_perf_counters, get_available_events_for_pmu


class SelfWattsController:
    """
    SelfWatts controller.
    """

    def __init__(self, hostname: str, pmu: str, db: DatabaseAdapter, sensor: HwpcSensorInvoker):
        self.hostname = hostname
        self.db = db
        self.pmu = pmu
        self.sensor = sensor
        self.available_perf_counters = get_available_perf_counters()
        self.available_events = self._get_available_events(pmu)

    def _get_available_events(self, pmu: str) -> List[str]:
        """
        Filter the list of available events.
        """
        def is_event_excluded(event: str) -> bool:
            """
            Returns True if the event is excluded, False otherwise.
            """
            if 'OFFCORE_RESPONSE' in event:
                return True
            if 'UOPS_DISPATCHED_PORT' in event:
                return True

            return False

        available_events = [event for event in get_available_events_for_pmu(pmu) if not is_event_excluded(event)]
        shuffle(available_events)
        return available_events

    def _generate_events_list(self, fixed_events: List[str]) -> List[str]:
        """
        Generate the events list to be monitored by the sensor.
        """
        available_slots = self.available_perf_counters - fixed_events.count(None)
        events = [fixed_event for fixed_event in fixed_events if fixed_event is not None]

        for _ in range(len(events), available_slots):
            if len(self.available_events) > 0:
                events.append(self.available_events.pop())

        return events

    def handle_control_events(self) -> None:
        """
        Handle the control events from the database.
        """
        logging.info('there is {} events and {} available performance counters'.format(len(self.available_events), self.available_perf_counters))
        logging.info('watching for control events from database...')
        while True:
            control_event = self.db.watch_control_event(self.hostname)
            logging.debug('received control event: {!r}'.format(control_event))
            self.sensor.stop()
            self.sensor.start(self._generate_events_list(control_event.parameters))


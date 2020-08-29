from pymongo import MongoClient

from selfwatts.controller.event import ControlEvent


class DatabaseAdapter:
    """
    Database Adapter abstract class.
    """

    def watch_control_event(self, hostname: str) -> ControlEvent:
        """
        Watch for new control events.
        """
        raise NotImplementedError()


class MongoDatabaseAdapter(DatabaseAdapter):
    """
    MongoDB database adatper class.
    """

    def __init__(self, uri: str, database: str, collection: str) -> None:
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.collection = self.db[collection]
        self.cursor = None

    def _setup_watch_cursor(self, hostname: str) -> None:
        """
        Setup the collection change stream cursor.
        """
        pipeline = [{'$match': {'operationType': 'insert'}}, {'$match': {'fullDocument.hostname': hostname}}]
        self.cursor = self.collection.watch(pipeline=pipeline)

    def watch_control_event(self, hostname: str) -> ControlEvent:
        """
        Watch for new control events.
        """
        if self.cursor == None:
            self._setup_watch_cursor(hostname)

        doc = next(self.cursor)['fullDocument']
        return ControlEvent(doc['timestamp'], doc['hostname'], doc['events'])




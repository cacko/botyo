import logging
import threading
from corethread import StoppableThread
from google.cloud.firestore import Client
from botyo.server.core import AppServer


delete_done = threading.Event()

# Create a callback on_snapshot function to capture changes


class DeleteListener(StoppableThread):

    def __init__(self, client: Client, *args, **kwargs):
        self.client = client
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        col_query = self.client.collection("users")
        query_watch = col_query.on_snapshot(self.on_snapshot)
        logging.info(query_watch)

    def on_snapshot(self, col_snapshot, changes, read_time):
        logging.debug(col_snapshot)
        for change in changes:
            match change.type.name:
                case 'REMOVED':
                    logging.info(f"removed {change.document.get().to_dict()}")
                    delete_done.set()


class CleaningServer(AppServer):
    def __init__(self, db: Client) -> None:
        worker = DeleteListener(client=db)
        super().__init__(worker)

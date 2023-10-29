import logging
from pathlib import Path
import threading
from typing import Optional
from corethread import StoppableThread
from google.cloud.firestore import Client, DocumentReference
from botyo.server.core import AppServer
from pydantic import BaseModel
from botyo.core.s3 import S3


delete_done = threading.Event()


class ItemPart(BaseModel):
    content: str
    type: str
    caption: Optional[str] = None
    contentType: Optional[str] = None


class HistoryItem(BaseModel):
    # title: Optional[str] = None
    # query: Optional[str] = None
    # method: Optional[str] = None
    # id: Optional[str] = None
    # timestamp: Optional[str] = None
    parts: Optional[list[ItemPart]] = None


class DeleteListener(StoppableThread):

    def __init__(self, client: Client, *args, **kwargs):
        self.client = client
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        for user_ref in self.client.collection("users").list_documents():
            try:
                assert isinstance(user_ref, DocumentReference)
                col_query = self.client.collection(f"users/{user_ref.id}/history")
                col_query.on_snapshot(self.on_snapshot)
            except AssertionError:
                pass

    def on_snapshot(self, col_snapshot, changes, read_time):
        logging.debug(col_snapshot)
        for change in changes:
            match change.type.name:
                case 'REMOVED':
                    doc = change.document
                    logging.info(f"removed {doc.to_dict()}")
                    self.handle_removed(HistoryItem(**doc.to_dict()))
                    delete_done.set()
                case 'MODIFIED':
                    pass

    def handle_removed(self, item: HistoryItem):
        if not item.parts:
            return
        for part in item.parts:
            if part.type == "image":
                pth = Path(part.content)
                S3.delete(pth.name.strip("/"))


class CleaningServer(AppServer):
    def __init__(self, db: Client) -> None:
        worker = DeleteListener(client=db)
        super().__init__(worker)

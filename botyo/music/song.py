import logging
from pathlib import Path
import os
from corestring import split_with_quotes, string_hash
from cachable.storage.file import FileStorage
from botyo.music.encoder import Encoder
from typing import Optional
from . import beets_library
from beets.library import Item


class Song:

    __query: Optional[str] = None
    __found: Optional[Path] = None
    __message: Optional[str] = None

    def __init__(self, query: str):
        self.__query = query
        self.load()

    def load(self):
        if not self.__search():
            raise FileNotFoundError
        if not self.__identify():
            raise FileNotFoundError
        if not self.__encode():
            raise FileNotFoundError

    def __search(self) -> Optional[Path]:
        if not self.__found:
            assert self.__query
            query = self.__query.strip()
            filt = split_with_quotes(query)
            if ":" not in query and len(filt) == 1:
                filt = [f"title:{filt[0]}"]
            items = list(beets_library.items(filt))
            assert len(items) > 0
            item = items[0]
            logging.debug(item)
            assert item
            self.__found = Path(item.path.decode())
            return self.__found
        return self.__found

    def __identify(self):
        if not self.__message:
            assert self.__found
            items = list(beets_library.items(f'path:"{self.__found.as_posix()}"'))
            assert len(items) > 0
            item = items[0]
            assert item
            logging.debug(item)
            self.__message = f"{item.artist} - {item.title}"
        return self.__message

    def __encode(self):
        if not self.destination.exists():
            assert self.__found
            Encoder.encode(self.__found, self.destination)
        return self.destination

    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=":".join(
                [
                    "/home/jago/miniforge3/bin",
                    "/home/jago/.local/bin",
                    "/usr/local/bin",
                    "/usr/bin",
                    "/bin",
                    "/usr/games",
                ]
            ),
        )

    @property
    def destination(self) -> Path:
        hash = string_hash(self.__query)
        return FileStorage.storage_path / f"{hash}.{Encoder.extension}"

    @property
    def message(self) -> str:
        return self.__message if self.__message else ""

    @property
    def filename(self) -> Path:
        return self.destination

    @property
    def content_type(self) -> str:
        return Encoder.content_type

    @property
    def duration(self) -> int:
        try:
            logging.info(self.destination.as_posix())
            items = list(beets_library.items(f'path:"{self.__found}"'))
            assert len(items) > 0
            item: Item = items[0]
            res = item.length
            assert res
            logging.info(f"duration={res}")
            return int(res)
        except Exception as e:
            logging.exception(e)
            return 0

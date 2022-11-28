from pathlib import Path
import os
from subprocess import PIPE, Popen, STDOUT
from corestring import split_with_quotes, string_hash
from cachable.storage.file import FileStorage
from app.music.encoder import Encoder
from typing import Optional

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
            with Popen(
                [
                    "conda",
                    "run",
                    "-n",
                    "base",
                    "--live-stream",
                    "beet",
                    "list",
                    "-p",
                    *filt,
                ],
                stdout=PIPE,
                stderr=STDOUT,
                env=self.environment,
            ) as p:
                assert p.stdout
                for line in iter(p.stdout.readline, b""):
                    print(line)
                    self.__found = Path(f"{line.decode().strip()}")
                    return self.__found
                if p.returncode:
                    print(p.returncode)
                    return
            return
        return self.__found

    def __identify(self):
        if not self.__message:
            assert self.__found
            cmd = (
                "ffprobe",
                "-loglevel",
                "error",
                "-show_entries",
                "format_tags=artist,title",
                "-of",
                "compact=item_sep='-':nokey=1:print_section=0",
                self.__found.as_posix(),
            )

            with Popen(
                cmd,
                stdout=PIPE,
                stderr=STDOUT,
                env=self.environment,
            ) as p:
                assert p.stdout
                for line in iter(p.stdout.readline, b""):
                    self.__message = line.decode().strip()
                    return self.__message
                if p.returncode:
                    return None
            return None
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

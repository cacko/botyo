from pathlib import Path
import os
from stringcase import alphanumcase
from subprocess import PIPE, Popen, STDOUT
from app.core.string import split_with_quotes
from cachable import Cachable
from app.music.encoder import Encoder, CODEC


class Song:

    __query: str = None
    __found: Path = None
    __message: Path = None
    __extension: str = "m4a"
    __content_type: str = "audio/mp4"

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

    def __search(self) -> Path:
        if not self.__found:
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
                for line in iter(p.stdout.readline, b""):
                    print(line)
                    self.__found = Path(f"{line.decode().strip()}")
                    return self.__found
                if p.returncode:
                    print(p.returncode)
                    return False
            return False
        return self.__found

    def __identify(self):
        if not self.__message:
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
                for line in iter(p.stdout.readline, b""):
                    self.__message = line.decode().strip()
                    return self.__message
                if p.returncode:
                    return None
            return None
        return self.__message

    def __encode(self):
        if not self.destination.exists():
            encoder = Encoder(self.__found, codec=CODEC.AAC)
            self.__content_type = encoder.content_type
            self.__extension = encoder.extension
            encoder.encode(self.destination)
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
        return Cachable.storage / f"{alphanumcase(self.__query)}.{self.__extension}"

    @property
    def message(self) -> str:
        return self.__message

    @property
    def filename(self) -> Path:
        return self.destination

    @property
    def content_type(self) -> str:
        return self.__content_type

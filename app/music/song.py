from pathlib import Path
import os
from subprocess import PIPE, Popen, STDOUT
from app.core.string import split_with_quotes
from cachable import Cachable
from app.music.encoder import Encoder, CODEC
from app.core.config import Config as app_config
from app.core.string import string_hash


class Song:

    __query: str = None
    __found: Path = None
    __message: Path = None

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
            encoder = Encoder(input_path=self.__found, codec=self.codec)
            encoder.encode(output_path=self.destination)
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
    def codec(self) -> CODEC:
        try:
            k = app_config.music.codec.upper()
            return CODEC[k]
        except ValueError:
            return CODEC.AAC

    @property
    def destination(self) -> Path:
        hash = string_hash(self.__query)
        return Cachable.storage / f"{hash}.{self.extension}"

    @property
    def message(self) -> str:
        return self.__message

    @property
    def filename(self) -> Path:
        return self.destination

    @property
    def extension(self) -> str:
        match (self.codec):
            case CODEC.OPUS:
                return "opus"
            case CODEC.AAC:
                return "m4a"
        return None

    @property
    def content_type(self) -> str:
        match (self.codec):
            case CODEC.OPUS:
                return "audio/ogg"
            case CODEC.AAC:
                return "audio/mp4"
        return None

from pathlib import Path
import os
from PIL import Image
from stringcase import alphanumcase
from subprocess import PIPE, Popen, STDOUT
from corestring import split_with_quotes
from cachable.storage.file import FileStorage
from typing import Optional


class AlbumArt:

    __query: str
    __found: Optional[Path] = None

    def __init__(self, query: str):
        self.__query = query
        self.load()

    def load(self):
        if not self.__search():
            raise FileNotFoundError
        if not self.__convert():
            raise FileNotFoundError

    def __search(self) -> Optional[Path]:
        if not self.__found:
            query = self.__query.strip()
            filt = split_with_quotes(query)
            with Popen(
                ["mamba", "run", "-n", "base", "--live-stream",
                    "beet", "list", "-p", "-a", *filt],
                stdout=PIPE,
                stderr=STDOUT,
                env=self.environment,
            ) as p:
                assert p.stdout
                for line in iter(p.stdout.readline, b""):
                    self.__found = Path(f"{line.decode().strip()}")
                    return self.__found
                if p.returncode:
                    return None
            return None
        return self.__found

    def __convert(self) -> bool:
        dst = self.destination
        if not dst.exists():
            assert self.__found
            p = self.__found / "cover.jpg"
            if not p.exists():
                return False
            im = Image.open(p)
            im.save(dst, format="png")
        return True

    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=":".join([
                "/home/jago/miniforge3/bin",
                "/home/jago/.local/bin",
                "/usr/local/bin",
                "/usr/bin",
                "/bin",
            ])
        )

    @property
    def destination(self) -> Path:
        filename = f"albumart-{alphanumcase(self.__query)}.png"
        return FileStorage.storage_path / filename

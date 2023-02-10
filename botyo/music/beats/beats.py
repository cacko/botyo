from pathlib import Path
from typing import Optional
from botyo.music.beats.db import BeatsDb
from cachable import Cachable
from cachable.request import Request
from corestring import string_hash
from .models.beats import Beats as BeatsModel
from botyo.core.bytes import nearest_bytes
from botyo.core.config import Config as app_config
import logging
from requests.exceptions import JSONDecodeError
from pydantic import BaseModel, Extra


class BeatsStruct(BaseModel, extra=Extra.ignore):
    path: Optional[str | Path] = None
    beats: Optional[list[float]] = None
    tempo: Optional[float] = None

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)


class Beats(Cachable):

    _id: Optional[str] = None
    __margin: int = 1
    __with_vocals: bool = True
    __force: bool = False
    __tmppath: Optional[Path] = None
    _struct: Optional[BeatsStruct] = None

    def __init__(
        self, path: str, hop_length=512, margin=0, with_vocals=False, force=False
    ) -> None:
        self.__path = self._resolve_path(path)
        self.__hop_length = hop_length
        self.__margin = nearest_bytes(margin)
        self.__with_vocals = with_vocals
        self.__force = force
        if not self.__path.exists():
            raise FileNotFoundError

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if self.__force:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    def fromcache(self):
        if model := BeatsModel.fetch(BeatsModel.path_id == self.id):
            return BeatsStruct(
                path=Path(model.path),
                beats=list(map(float, model.beats)),
                tempo=model.tempo,
            )
        return None

    def tocache(self, res: BeatsStruct):
        with BeatsDb.db.atomic():
            assert res
            assert isinstance(res.path, Path)
            BeatsModel.insert(
                path=res.path.as_posix(),
                path_id=self.id,
                beats=res.beats,
                tempo=res.tempo,
            ).on_conflict(
                conflict_target=[BeatsModel.path_id],
                update={BeatsModel.beats: res.beats,
                        BeatsModel.tempo: res.tempo},
            ).execute()
        return res

    def _resolve_path(self, path):
        res = Path(path)
        return res

    @property
    def id(self):
        if not self._id:
            self._id = string_hash(self.__path.as_posix())
        return self._id

    def _load(self):
        try:
            rs = Request(
                url=app_config.beats.extractor_url,
                params={
                    "path": self.__path.as_posix(),
                    "hop_length": self.__hop_length,
                    "margin": self.__margin,
                    "with_vocals": self.__with_vocals,
                },
            )
            assert rs.json
            self._struct = BeatsStruct(**rs.json)
            return self.tocache(self._struct)
        except JSONDecodeError as e:
            logging.error(e)

    @property
    def model(self) -> BeatsStruct:
        if not self.load():
            self._load()
        assert self._struct
        return self._struct

    @property
    def tempo(self) -> float:
        if not self.load():
            self._load()
        assert self._struct
        assert self._struct.tempo
        return self._struct.tempo

    @property
    def path(self) -> str:
        if not self.load():
            self._load()
        assert self._struct
        assert isinstance(self._struct.path, Path)
        return self._struct.path.as_posix()

    @property
    def beats(self) -> list[float]:
        if not self.load():
            self._load()
        else:
            logging.debug(f"Loading beats for {self.__path} from cache")
        assert self._struct
        assert self._struct.beats
        return self._struct.beats

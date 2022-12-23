from datetime import datetime, timezone
from dataclasses import dataclass, field
from marshmallow import fields
from dataclasses_json import dataclass_json, Undefined, config
from typing import Optional
from coretime import isodate_decoder, isodate_encoder
from botyo.core.store import RedisStorage
import pickle
from cachable.storage.file import FileStorage
from pathlib import Path
from stringcase import alphanumcase
from base64 import b64decode
from botyo.music.encoder import Encoder

from botyo.music.encoder import Encoder


class TrackMeta(type):

    __TRACK_STORAGE_KEY = "now_playing_track"
    __instance: Optional["Track"] = None

    def __call__(cls, *args, **kwds):
        cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    def persist(cls):
        if not cls.__instance:
            return
        dc = cls.__instance
        st_key = cls.storage_key
        RedisStorage.pipeline().set(st_key, pickle.dumps(dc.to_dict())).persist(  # type: ignore
            st_key
        ).execute()

    def load(cls):
        st_key = cls.storage_key
        data = RedisStorage.get(st_key)
        if data:
            dc = pickle.loads(data)
            return cls(**dc)
        return None

    @property
    def trackdata(cls) -> Optional["Track"]:
        if cls.__instance:
            return cls.__instance
        return cls.load()

    @property
    def storage_key(cls):
        return cls.__TRACK_STORAGE_KEY


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Track(metaclass=TrackMeta):
    id: str
    parent: str
    isDir: bool
    title: str
    album: str
    artist: str
    duration: int
    size: int
    created: datetime = field(
        metadata=config(
            encoder=isodate_encoder,
            decoder=isodate_decoder,
            mm_field=fields.DateTime(format="iso", tzinfo=timezone.utc),
        )
    )
    albumId: Optional[str] = None
    artistId: Optional[str] = None
    track: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    coverArt: Optional[str] = None
    coverArtIcon: Optional[str] = None
    contentType: Optional[str] = None
    suffix: Optional[str] = None
    bitRate: Optional[int] = None
    path: Optional[str] = None
    discNumber: Optional[int] = None

    @property
    def audio_destination(self) -> Path:
        assert self.path
        song_path = Path(self.path)
        name = "/".join([song_path.parent.name, song_path.stem])
        res = FileStorage.storage_path / f"{alphanumcase(name)}.{Encoder.extension}"
        if not res.exists():
            Encoder.encode(song_path, res)
        return res

    @property
    def message(self) -> str:
        return f"{self.artist} / {self.title}"

    @property
    def album_art(self) -> Path:
        name = "/".join([self.artist, self.album])
        res = FileStorage.storage_path / f"albumart-{alphanumcase(name)}.png"
        if not res.exists():
            assert self.coverArt
            data = b64decode(self.coverArt)
            res.write_bytes(data)
        return res

    @property
    def audio_content_type(self) -> str:
        return Encoder.content_type

    @property
    def art_content_type(self) -> str:
        return "image/png"
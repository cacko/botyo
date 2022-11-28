from cachable.request import Request
from hashlib import blake2b
from cachable.storage.file import CachableFileImage
from cachable import Cachable
from cachable.models import BinaryStruct
from urllib.parse import quote
from app.core.config import Config
from app.core.image import pixelme_b64
from typing import Optional

class Team(CachableFileImage):

    _struct: Optional[BinaryStruct] = None
    __name: str
    __id = None
    SIZE = (200, 200)
    __apiUrl: str

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__name = name
        self.__apiUrl = Config.ontv.api_url

    def _init(self):
        if self.isCached:
            return
        try:
            req = Request(
                f"{self.__apiUrl}/assets/team/badge/{quote(self.__name)}.png"
            )
            return self.tocache(req.binary)
        except Exception:
            pass

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def filename(self) -> str:
        return f"{self.id}.png"


class TeamLogoPixel(Cachable):

    __name: str
    __id = None

    def __init__(self, name) -> None:
        self.__name = name

    @property
    def base64(self) -> str:
        if not self.load():
            team = Team(self.__name)
            path = team.path
            self._struct = pixelme_b64(path, resize=(8, 8))
            self.tocache(self._struct)
        return self._struct

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

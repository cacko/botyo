from typing import Any
from uuid import uuid4
from botyo.core.config import Config as app_config
from pathlib import Path
from shutil import copy


class KonkatMeta(type):

    __instance: 'Konkat'

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls.__instance:
            cls.__instance = type.__call__(
                cls,
                Path(app_config.cachable.path)
            )
        return cls.__instance

    def upload(cls, tmp_path: Path, collage_id: str) -> str:
        return cls().do_upload(tmp_path)

    def collage(cls, collage_id: str) -> Path:
        return cls().get_collage(collage_id)


class Konkat(object, metaclass=KonkatMeta):

    def __init__(self, storage: Path) -> None:
        self.__storage = storage

    def do_upload(self, tmp_path: Path, collage_id: str) -> str:
        file_id = f"{collage_id}__{uuid4().hex}"
        file_dst = self.__storage / f"{file_id}{tmp_path.suffix}"
        copy(tmp_path.as_posix(), file_dst.as_posix())
        return file_id

    def get_collage(self, collage_id: str) -> Path:
        return Path(".")

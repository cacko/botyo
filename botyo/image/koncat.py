from typing import Any, Generator, Optional
from uuid import uuid4
from botyo.core.config import Config as app_config
from pathlib import Path
from shutil import copy
from botyo.core.s3 import S3
from corefile import filepath

from botyo.image.models import KonkatFile


class KonkatMeta(type):

    _instance: Optional['Konkat'] = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls._instance:
            cls._instance = type.__call__(
                cls,
                Path(app_config.cachable.path)
            )
        return cls._instance

    def upload(cls, tmp_path: Path, collage_id: str) -> KonkatFile:
        return cls().do_upload(tmp_path, collage_id)

    def collage(cls, collage_id: str) -> Path:
        return cls().get_collage(collage_id)

    def files(cls, collage_id: str) -> list[KonkatFile]:
        return [kf for kf in cls().get_files(collage_id)]

    def delete(cls, filename: str):
        return cls().do_delete(filename)


class Konkat(object, metaclass=KonkatMeta):

    def __init__(self, storage: Path) -> None:
        self.__storage = storage

    def do_upload(self, tmp_path: Path, collage_id: str) -> KonkatFile:
        file_name = f"{collage_id}__{uuid4().hex}{tmp_path.suffix}"
        file_dst = self.__storage / file_name
        copy(tmp_path.as_posix(), file_dst.as_posix())
        s3key = S3.upload(file_dst, file_name)
        return KonkatFile(
            collage_id=collage_id,
            filename=file_name,
            url=f"https://cdn.alex.net/{s3key}"
        )

    def get_collage(self, collage_id: str) -> Path:
        return Path(".")

    def get_files(self, collage_id: str) -> Generator[KonkatFile, None, None]:
        for f in filepath(root=self.__storage, prefix=f"{collage_id}_"):
            yield KonkatFile(
                collage_id=collage_id,
                filename=f.name,
                url=f"https://cdn.alex.net/{S3.src_key(f.name)}"
            )

    def do_delete(self, filename: str):
        pass

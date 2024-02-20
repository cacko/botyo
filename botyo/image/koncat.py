from typing import Any, Generator
from uuid import uuid4
from botyo.core.config import Config as app_config
from pathlib import Path
from shutil import copy, move
from botyo.core.s3 import S3
from corefile import filepath
from filetype import guess_extension
from coreimage.organise.concat import Concat
from PIL.ImageOps import exif_transpose
from PIL import Image
from botyo.image.models import KonkatFile


class KonkatMeta(type):

    def __call__(cls, *args: Any, **kwds: Any) -> Any:

        return type.__call__(
            cls,
            Path(app_config.cachable.path)
        )

    def upload(cls, tmp_path: Path, collage_id: str) -> KonkatFile:
        return cls().do_upload(tmp_path, collage_id)

    def collage(cls, collage_id: str, shuffle: bool = False) -> KonkatFile:
        return cls().get_collage(collage_id, shuffle)

    def files(cls, collage_id: str) -> list[KonkatFile]:
        return [kf for kf in cls().get_files(collage_id)]

    def delete(cls, filename: str):
        return cls().do_delete(filename)


class Konkat(object, metaclass=KonkatMeta):

    def __init__(self, storage: Path) -> None:
        self.__storage = storage

    def do_upload(self, tmp_path: Path, collage_id: str) -> KonkatFile:
        extension = guess_extension(tmp_path.as_posix())
        file_name = f"{collage_id}__{uuid4().hex}.{extension}"
        file_dst = self.__storage / file_name
        with Image.open(tmp_path.as_posix()) as img:
            print(img.getexif())
            exif_transpose(img, in_place=True)
            img.save(file_dst.as_posix())
        s3key = S3.upload(file_dst, file_name)
        return KonkatFile(
            collage_id=collage_id,
            filename=file_name,
            url=f"https://cdn.cacko.net/{s3key}"
        )

    def get_collage(self, collage_id: str, shuffle: bool = False) -> KonkatFile:
        filename = f"collage_{collage_id}.webp"
        file_dst = self.__storage / filename
        input_path = f"{self.__storage.as_posix()}/{collage_id}*"
        collage_path, collage_hash = Concat(file_dst).concat_from_paths([
            Path(input_path)
        ], shuffle=shuffle)
        filename = f"koncat_{collage_id}_{collage_hash}.webp"
        file_dst = self.__storage / filename
        move(collage_path.as_posix(), file_dst.as_posix())
        s3key = S3.upload(file_dst, filename)
        return KonkatFile(
            collage_id=collage_id,
            filename=filename,
            url=f"https://cdn.cacko.net/{s3key}"
        )

    def get_files(self, collage_id: str) -> Generator[KonkatFile, None, None]:
        for f in filepath(root=self.__storage, prefix=f"{collage_id}_"):
            yield KonkatFile(
                collage_id=collage_id,
                filename=f.name,
                url=f"https://cdn.cacko.net/{S3.src_key(f.name)}"
            )

    def do_delete(self, filename: str) -> bool:
        file_dst = self.__storage / filename
        if file_dst.exists():
            file_dst.unlink()
        return S3.delete(file_dst.name)

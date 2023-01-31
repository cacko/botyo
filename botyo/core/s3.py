import boto3
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO
from pathlib import Path
from botyo.core.config import Config as app_config
import filetype


class S3Upload(BaseModel):
    src: str
    dst: str
    skip_upload: bool = Field(default=False)


class S3Meta(type):
    def __call__(cls, *args, **kwds):
        return type.__call__(cls, *args, **kwds)

    def upload(cls, item: S3Upload) -> tuple[str, str, str, str]:
        return cls().upload_file(item.src, item.dst, item.skip_upload)

    def thumb(cls, item: S3Upload) -> tuple[str, str, str, str]:
        thumb = cls().upload_thumb(item.src, item.dst, item.skip_upload)
        folder = Path(item.dst).parent.as_posix()
        return folder, item.src, cls.src_key(item.dst), thumb

    def src_key(cls, dst):
        return f"{app_config.s3.directory}/{dst}"


class S3(object, metaclass=S3Meta):
    _client: boto3.client = None
    THUMB_SIZE = (300, 300)

    def __init__(self) -> None:
        self._client = boto3.client(service_name="s3", **app_config.s3.dict())

    def upload_thumb(self, src, dst, skip_upload=False):
        dst_thumb = Path(self.__class__.src_key(dst))
        dst_thumb = (
            dst_thumb.parent
            / f"{dst_thumb.stem}_{'x'.join(map(str, self.THUMB_SIZE))}.webp"
        )
        dst_thumb = dst_thumb.as_posix()
        if skip_upload:
            return dst_thumb
        bucket = app_config.s3.storage_bucket_name
        img = Image.open(src)
        img.thumbnail(self.THUMB_SIZE)
        byte_io = BytesIO()
        img.save(byte_io, "WEBP")
        byte_io.seek(0)
        self._client.upload_fileobj(
            byte_io,
            bucket,
            dst_thumb,
            ExtraArgs={"ContentType": "image/webp", "ACL": "public-read"},
        )
        return dst_thumb

    def upload_file(self, src, dst, skip_upload=False) -> tuple[str, str, str, str]:
        mime = filetype.guess_mime(src)
        folder = Path(dst).parent.as_posix()
        if not skip_upload:
            bucket = app_config.s3.storage_bucket_name
            self._client.upload_file(
                src,
                bucket,
                self.__class__.src_key(dst),
                ExtraArgs={"ContentType": mime, "ACL": "public-read"},
            )
        dst_thumb = self.upload_thumb(src, dst, skip_upload)
        return folder, src, self.__class__.src_key(dst), dst_thumb

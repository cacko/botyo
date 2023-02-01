import boto3
from pathlib import Path
from botyo.core.config import Config as app_config
import filetype


class S3Meta(type):
    def __call__(cls, *args, **kwds):
        return type.__call__(cls, *args, **kwds)

    def upload(cls, src: Path, dst: str, skip_upload: bool = False) -> str:
        return cls().upload_file(src, dst, skip_upload)

    def src_key(cls, dst):
        return f"{app_config.s3.directory}/{dst}"


class S3(object, metaclass=S3Meta):
    _client: boto3.client = None

    def __init__(self) -> None:
        self._client = boto3.client(service_name="s3", **app_config.s3.dict())

    def upload_file(self, src: Path, dst, skip_upload=False) -> str:
        mime = filetype.guess_mime(src)
        key = self.__class__.src_key(dst)
        if not skip_upload:
            bucket = app_config.s3.storage_bucket_name
            self._client.upload_file(
                src,
                bucket,
                key,
                ExtraArgs={"ContentType": mime, "ACL": "public-read"},
            )
        return key

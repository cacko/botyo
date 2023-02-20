from distutils.command.build import build
import boto3
from pathlib import Path
from botyo.core.config import Config as app_config
import filetype
import logging


class S3Meta(type):
    def __call__(cls, *args, **kwds):
        return type.__call__(cls, *args, **kwds)

    def upload(cls, src: Path, dst: str, skip_upload: bool = False) -> str:
        logging.debug(f"upload {src} to {dst}")
        return cls().upload_file(src, dst, skip_upload)

    def src_key(cls, dst):
        return f"{app_config.s3.directory}/{dst}"


class S3(object, metaclass=S3Meta):

    def __init__(self) -> None:
        cfg = app_config.s3
        self._client = boto3.client(
            service_name="s3",
            aws_access_key_id=cfg.aws_access_key_id,
            aws_secret_access_key=cfg.aws_secret_access_key,
            region_name=cfg.region_name,
        )

    def upload_file(self, src: Path, dst, skip_upload=False) -> str:
        mime = filetype.guess_mime(src)
        key = self.__class__.src_key(dst)
        if not skip_upload:
            bucket = app_config.s3.storage_bucket_name
            res = self._client.upload_file(
                src,
                bucket,
                key,
                ExtraArgs={"ContentType": mime, "ACL": "public-read"},
            )
            logging.debug(res)
        return key

    def delete_file(self, file_name: str) -> bool:
        bucket = app_config.s3.storage_bucket_name
        return self._client.delete_object(Bucket=bucket, Key=file_name)

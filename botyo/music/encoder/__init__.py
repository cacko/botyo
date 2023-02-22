from enum import IntEnum
from pathlib import Path
from subprocess import call
import shlex
import os
import logging
from botyo.core.config import Config as app_config
from typing import Optional


class CODEC(IntEnum):
    OPUS = 1
    AAC = 2


class EncodeMeta(type):
    __instance: Optional["Encoder"] = None

    def __call__(cls, *args, **kwds):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    @property
    def codec(cls) -> CODEC:
        try:
            k = app_config.music.codec.upper()
            return CODEC[k]
        except ValueError:
            return CODEC.AAC

    @property
    def extension(cls) -> str:
        match (cls.codec):
            case CODEC.OPUS:
                return "opus"
            case CODEC.AAC:
                return "m4a"
        raise AssertionError("not suported")

    @property
    def content_type(cls) -> str:
        match (cls.codec):
            case CODEC.OPUS:
                return "audio/ogg"
            case CODEC.AAC:
                return "audio/mp4"
        raise AssertionError("not support content type")

    def encode(cls, input_path: Path, output_path: Path):
        return cls().do_encode(input_path=input_path, output_path=output_path)


class Encoder(object, metaclass=EncodeMeta):
    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=":".join(
                [
                    "/home/jago/miniforge3/bin",
                    "/home/jago/.local/bin",
                    "/usr/local/bin",
                    "/usr/bin",
                    "/bin",
                    "/usr/games",
                ]
            ),
        )

    def get_cmd(self, input_path: Path, output_path: Path) -> tuple[str]:
        match (Encoder.codec):
            case CODEC.OPUS:
                return (
                    "ffmpeg",
                    "-loglevel",
                    "quiet",
                    "-stats",
                    "-i",
                    input_path.as_posix(),
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "64k",
                    "-movflags",
                    "+faststart",
                    "-vn",
                    "-y",
                    output_path.as_posix(),
                )
            case CODEC.AAC:
                return (
                    "ffmpeg",
                    "-loglevel",
                    "quiet",
                    "-stats",
                    "-i",
                    input_path.as_posix(),
                    "-c:a",
                    "libfdk_aac",
                    "-profile:a",
                    "aac_he_v2",
                    "-b:a",
                    "64k",
                    "-movflags",
                    "+faststart",
                    "-vn",
                    "-y",
                    output_path.as_posix(),
                )
        return None

    def do_encode(self, input_path: Path, output_path: Path):
        cmd = self.get_cmd(input_path=input_path, output_path=output_path)
        logging.debug(shlex.join(cmd))
        retcode = call(shlex.join(cmd), shell=True, env=self.environment)
        if retcode:
            return None
        return output_path

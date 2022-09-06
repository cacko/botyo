from enum import IntEnum
from pathlib import Path
from subprocess import call
import shlex
import os
from app.core import logger


class CODEC(IntEnum):
    OPUS = 1
    AAC = 2


class Encoder:

    __input_path: Path = None

    def __init__(self, input_path: Path) -> None:
        self.__input_path = input_path

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

    def encode(self, output_path, codec: CODEC = CODEC.AAC):
        match (codec):
            case CODEC.OPUS:
                cmd = (
                    "ffmpeg",
                    "-loglevel",
                    "quiet",
                    "-stats",
                    "-i",
                    self.__input_path.as_posix(),
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
                cmd = (
                    "ffmpeg",
                    "-loglevel",
                    "quiet",
                    "-stats",
                    "-i",
                    self.__input_path.as_posix(),
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
        logger.warning(shlex.join(cmd))
        retcode = call(shlex.join(cmd), shell=True, env=self.environment)
        if retcode:
            return None
        return output_path

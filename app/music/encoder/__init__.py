from enum import IntEnum
from pathlib import Path
from subprocess import call
import shlex
import os
from app.core import logger


class CODEC(IntEnum):
    OPUS = 1
    AAC = 2


class Encoder(object):

    __input_path: Path = None
    __codec: CODEC = None

    def __init__(self, input_path: Path, codec: CODEC = None):
        self.__input_path = input_path
        self.__codec = codec

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

    def get_cmd(self, output_path: Path) -> tuple[str]:
        match (self.__codec):
            case CODEC.OPUS:
                return (
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
                return (
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
        return None

    def encode(self, output_path: Path):
        cmd = self.get_cmd(output_path=output_path)
        logger.warning(shlex.join(cmd))
        retcode = call(shlex.join(cmd), shell=True, env=self.environment)
        if retcode:
            return None
        return output_path

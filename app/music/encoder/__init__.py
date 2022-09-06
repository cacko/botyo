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
    __codec: CODEC = None

    def __init__(self, input_path: Path, codec: CODEC = None) -> None:
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

    @property
    def extension(self) -> str:
        match (self.__codec):
            case CODEC.OPUS:
                return "opus"
            case CODEC.AAC:
                return "m4a"
        return None

    @property
    def content_type(self) -> str:
        match (self.__codec):
            case CODEC.OPUS:
                return "audio/ogg"
            case CODEC.AAC:
                return "audio/mp4"
        return None

    @property
    def cmd(self) -> list[str]:
        match (self.__codec):
            case CODEC.OPUS:
                return [
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
                ]
            case CODEC.AAC:
                return [
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
                ]
        return None

    def encode(self, output_path: Path):
        exec_cmd = tuple(self.cmd + [output_path.as_posix()])
        logger.warning(shlex.join(exec_cmd))
        retcode = call(shlex.join(exec_cmd), shell=True, env=self.environment)
        if retcode:
            return None
        return output_path

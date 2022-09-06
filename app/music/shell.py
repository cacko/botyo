from app.core import logger
from subprocess import PIPE, Popen, STDOUT, call
import os
from typing import Generator
import shlex


class ShellMeta(type):
    def __call__(cls, *args, **kwargs):
        return type.__call__(cls, *args, **kwargs)

    def output(cls, *args) -> Generator[str, None, None]:
        yield from cls(*args).getOutput()


class Shell(object, metaclass=ShellMeta):

    args: list[str] = None

    executable: str = None
    executable_arguments: list[str] = []

    OUTPUT_IGNORED = []
    OUTPUT_REPLACED = []

    def __init__(self, args: str):
        self.args = shlex.split(args)
        self.__post_init__()

    def __post_init__(self):
        pass

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

    def getOutput(self) -> Generator[str, None, None]:
        cmd = (self.executable, *self.executable_arguments, *self.args)
        logger.debug(cmd)
        with Popen(
            cmd,
            stdout=PIPE,
            stderr=STDOUT,
            env=self.environment,
        ) as p:
            for line in iter(p.stdout.readline, b""):
                line = line.decode().strip()
                if any([x in line for x in self.OUTPUT_IGNORED]):
                    continue
                if prefix := next(
                    filter(lambda x: line.startswith(x), self.OUTPUT_REPLACED), None
                ):
                    line = line.removeprefix(prefix).strip()
                    line = f"{line.upper()}\n"
                yield line
            if p.returncode:
                return None

    def execute(self):
        cmd = [self.executable, *self.executable_arguments, *self.args]
        logger.debug(shlex.join(cmd))
        return call(shlex.join(cmd), shell=True, env=self.environment)
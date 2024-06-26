from subprocess import Popen, PIPE, STDOUT
import os
from typing import Optional

from botyo.server.output import TextOutput


class BaseMeta(type):
    @property
    def executable(cls):
        return cls.command


class Base(object, metaclass=BaseMeta):

    args: list[str] = []

    def __init__(self, query: str):
        self.args = query.strip("`").split(" ")
        self.validate()

    def validate(self):
        raise NotImplementedError

    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=":".join(["/home/jago/.pyenv/plugins/pyenv-virtualenv/shims",
                           "/home/jago/",
                           ".pyenv/shims",
                           "/home/jago/.pyenv/bin",
                           "/home/jago/.local/bin",
                           "/usr/local/bin",
                           "/usr/bin:/bin:/usr/games"])
        )

    @property
    def text(self) -> Optional[str]:
        with Popen(
            [self.__class__.executable, *self.args],
            stdout=PIPE,
            stderr=STDOUT,
            env=self.environment,
        ) as p:
            assert p.stdout
            for line in iter(p.stdout.readline, b""):
                lnt = line.decode().strip()
                TextOutput.addRows([lnt])
            if p.returncode:
                return None
        return TextOutput.render()

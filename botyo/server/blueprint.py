import logging
from botyo.server.models import Method, ZSONMatcher, ZSONOption
from .server import Server, CommandExec
from typing import Optional


def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


class BlueprintMeta(type):
    _instances: dict[str, "Blueprint"] = {}

    def __call__(cls, *args, **kwds):
        name = kwds.get("name") if "name" in kwds else args[0]
        if not name:
            raise NotImplementedError
        if name not in cls._instances:
            cls._instances[name] = type.__call__(cls, *args, **kwds)
        return cls._instances[name]


class Blueprint(object, metaclass=BlueprintMeta):
    _name: Optional[str] = None
    _app: Optional["Server"] = None
    _commands: dict[str, CommandExec] = {}

    def __init__(self, name):
        self._name = name

    def register(self, app: "Server"):
        logging.debug(f"registaring {self._name}")
        self._app = app
        if not len(self._commands):
            return
        for cmd in self._commands.values():
            self._app.register(cmd)

    @property
    def registered(cls):
        return cls._app is not None

    @parametrized
    def command(
        func,
        self,
        method: Method,
        desc: Optional[str] = None,
        subscription: bool = False,
        icon: Optional[str] = None,
        args: Optional[str] = None,
        uses_prompt: bool = False,
        upload: bool = False,
        matcher: Optional[ZSONMatcher] = None,
        response: Optional[str] = None,
        options: Optional[list[ZSONOption]] = None
    ):
        if method.value not in self._commands:
            cmd = CommandExec(
                method=method,
                handler=func,  # type: ignore
                desc=desc,
                matcher=matcher,
                response=response,
                subscription=subscription,
                icon=icon,
                args=args,
                upload=upload,
                uses_prompt=uses_prompt,
                options=options
            )
            self._commands[method.value] = cmd

        def registrar(*args):
            return func(*args)  # type: ignore

        return registrar

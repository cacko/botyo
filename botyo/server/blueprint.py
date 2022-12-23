import logging
from botyo.server.models import Method, ZSONMatcher
from .server import Server, CommandExec

def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)
        return repl
    return layer


class BlueprintMeta(type):

    _instances: dict[str, 'Blueprint'] = {}

    def __call__(cls, *args, **kwds):
        name = kwds.get("name") if "name" in kwds else args[0]
        if not name:
            raise NotImplementedError
        if name not in cls._instances:
            cls._instances[name] = type.__call__(cls, *args, **kwds)
        return cls._instances[name]


class Blueprint(object, metaclass=BlueprintMeta):

    _name: str = None
    _app: 'Server' = None
    _commands: dict[str, CommandExec] = {}

    def __init__(self, name):
        self._name = name

    def register(self, app: 'Server'):
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
        desc: str = None,
        matcher: ZSONMatcher = None,
        response: str = None
    ):
        if method.value not in self._commands:
            cmd = CommandExec(
                method=method,
                handler=func,
                desc=desc,
                matcher=matcher,
                response=response,
            )
            self._commands[method.value] = cmd

        def registrar(*args):
            return func(*args)

        return registrar

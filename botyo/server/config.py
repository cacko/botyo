import errno
import types
import typing as t
import sys
from pathlib import Path


def import_string(import_name: str, silent: bool = False) -> t.Any:
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e) from None

    except ImportError as e:
        if not silent:
            raise ValueError(import_name, e).with_traceback(
                sys.exc_info()[2]
            ) from None

    return None


class ConfigAttribute:
    """Makes an attribute forward to the config"""

    def __init__(
        self,
        name: str,
        get_converter: t.Optional[t.Callable] = None
    ):
        self.__name__ = name
        self.get_converter = get_converter

    def __get__(self, obj: t.Any, owner: t.Any = None) -> t.Any:
        if obj is None:
            return self
        rv = obj.config[self.__name__]
        if self.get_converter is not None:
            rv = self.get_converter(rv)
        return rv

    def __set__(self, obj: t.Any, value: t.Any) -> None:
        obj.config[self.__name__] = value


class Config(dict):

    def __init__(self, root_path: Path, defaults: t.Optional[dict] = None):
        dict.__init__(self, defaults or {})
        self.root_path = root_path / "instance"

    def from_pyfile(self, filename: str, silent: bool = False) -> bool:
        filename = (self.root_path / filename).absolute().as_posix()
        d = types.ModuleType("config")
        d.__file__ = filename
        try:
            with open(filename, mode="rb") as config_file:
                exec(compile(config_file.read(), filename, "exec"), d.__dict__)
        except OSError as e:
            if silent and e.errno in (
                    errno.ENOENT,
                    errno.EISDIR,
                    errno.ENOTDIR):
                return False
            e.strerror = f"Unable to load configuration file ({e.strerror})"
            raise
        self.from_object(d)
        return True

    def from_object(self, obj: t.Union[object, str]) -> None:
        if isinstance(obj, str):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def get_namespace(
        self,
        namespace: str,
        lowercase:
        bool = True,
        trim_namespace: bool = True
    ) -> t.Dict[str, t.Any]:
        rv = {}
        for k, v in self.items():
            if not k.startswith(namespace):
                continue
            if trim_namespace:
                key = k[len(namespace):]
            else:
                key = k
            if lowercase:
                key = key.lower()
            rv[key] = v
        return rv

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {dict.__repr__(self)}>"

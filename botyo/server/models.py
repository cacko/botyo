from dataclasses import dataclass
from uuid import uuid4
from dataclasses_json import dataclass_json, Undefined
from typing import Optional
from emoji import emojize
from random import choice
from enum import EnumMeta, Enum
from pathlib import Path
import sys
import requests


class MethodMeta(EnumMeta):

    _enums = {}

    def __new__(metacls, cls, bases, classdict,  **kwds):
        for x in classdict._member_names:
            metacls._enums[classdict[x]] = ".".join(
                [classdict["__module__"], cls])
        return super().__new__(metacls, cls, bases, classdict, **kwds)

    def __call__(cls, value, names=None, *, module=None, qualname=None, type=None, start=1):
        if names is None:  # simple value lookup
            klass = cls._enums[value]
            papp = Path(".") / "app"
            enumklass = klass.split(".")[-1]
            if enumklass == cls.__name__:
                return cls.__new__(cls, value)
            if klass.startswith("app."):
                sys.path.insert(0, papp)
                mod = ".".join(klass.split(".")[:-1])
                imp = __import__(mod, None, None, [enumklass])
                return getattr(imp, enumklass)(value)
            return eval(f"{enumklass}(\"{value}\")")
        return cls._create_(
            value,
            names,
            module=module,
            qualname=qualname,
            type=type,
            start=start,
        )


class Method(Enum, metaclass=MethodMeta):

    def __eq__(self, __o: object) -> bool:
        return self.value == __o.value


class CoreMethods(Method, Enum):
    LOGIN = "login"
    HELP = "help"


class ZSONMatcher(Enum):
    PHRASE = "phrase"
    SOURCE = "source"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandDef:
    method: Method
    desc: Optional[str] = None
    response:  Optional[str] = None
    matcher:  Optional[ZSONMatcher] = None

    @property
    def namespace(self) -> str:
        return self.method.value.split(":", 2)[0].strip()

    @property
    def action(self) -> str:
        return self.method.value.split(":")[-1].strip()


class ZSONType(Enum):
    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class Attachment:
    path: Optional[str] = None
    contentType: Optional[str] = None
    duration: Optional[int] = 0
    filename: Optional[str] = None

    def __post_init__(self):
        if self.filename:
            self.path = self.filename
        elif self.path:
            self.filename = Path(self.path).name


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RenderResult:
    method: Optional[Method] = None
    message: Optional[str] = ""
    attachment: Optional[Attachment] = None
    group: Optional[str] = None
    plain: Optional[bool] = False


NOT_FOUND = [
    "Няма нищо брат",
    "Отиде коня у реката",
    "...and the horse went into the river",
    "Go fish!",
    "Nod fand!",
]

NOT_FOUND_ICONS = [
    ':axe:',
    ':thinking_face:',
    ':open_hands:',
    ':horse_face: :bucket:',
    ':man_walking: :left_arrow:'
]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EmptyResult(RenderResult):

    @property
    def error_message(self):
        try:
            return requests.get('https://commit.cacko.net/index.txt').text.strip()
        except Exception:
            return choice(NOT_FOUND)

    def __post_init__(self):
        self.message = f"{emojize(choice(NOT_FOUND_ICONS))} {self.error_message}"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONError:
    code: int
    message: str
    meaning: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONMessage:
    ztype: Optional[ZSONType] = None
    id: Optional[str] = None
    client: Optional[str] = None
    group: Optional[str] = None
    method: Optional[Method] = None
    source: Optional[str] = None

    def __post_init__(self):
        self.id = uuid4().hex

    def encode(self) -> bytes:
        return self.to_json().encode()  # type: ignore


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONResponse(ZSONMessage):
    error: Optional[ZSONError] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    ztype: ZSONType = ZSONType.RESPONSE
    commands: Optional[list[CommandDef]] = None
    plain: Optional[bool] = False

    @property
    def attachment_path(self) -> Optional[Path]:
        if not self.attachment:
            return None
        if not self.attachment.path:
            return None
        res = Path(self.attachment.path)
        return res if res.exists() else None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONRequest(ZSONMessage):
    source: Optional[str] = None
    lang: Optional[str] = None
    query: Optional[str] = None
    utf8mono: Optional[bool] = True
    attachment: Optional[Attachment] = None
    ztype: ZSONType = ZSONType.REQUEST


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass

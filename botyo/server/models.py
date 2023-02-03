from uuid import uuid4
from typing import Optional, TypeVar
from emoji import emojize
from random import choice
from enum import EnumMeta, StrEnum, Enum
from pathlib import Path
import sys
import requests
from pydantic import BaseModel, Extra, Field


class MethodMeta(EnumMeta):

    _enums = {}

    def __new__(metacls, cls, bases, classdict, **kwds):
        for x in classdict._member_names:
            metacls._enums[classdict[x]] = ".".join(
                [classdict["__module__"], cls])
        return super().__new__(metacls, cls, bases, classdict, **kwds)

    def __call__(cls,
                 value,
                 names=None,
                 *,
                 module=None,
                 qualname=None,
                 type=None,
                 start=1):
        if names is None:  # simple value lookup
            klass = cls._enums[value]
            papp = Path(".") / "app"
            enumklass = klass.split(".")[-1]
            if enumklass == cls.__name__:
                return cls.__new__(cls, value) #type: ignore
            if klass.startswith("app."):
                sys.path.insert(0, papp) #type: ignore
                mod = ".".join(klass.split(".")[:-1])
                imp = __import__(mod, None, None, [enumklass])
                return getattr(imp, enumklass)(value)
            return eval(f'{enumklass}("{value}")')
        return cls._create_( #type: ignore
            value,
            names,
            module=module,
            qualname=qualname,
            type=type,
            start=start,
        )


class ZMethod(StrEnum, metaclass=MethodMeta):
    LOGIN = "login"
    KNOWLEDGE_ARTICLE = "kb:article"
    KNOWLEDGE_ASK = "kb:ask"
    KNOWLEDGE_TELL = "kb:tell"
    KNOWLEDGE_WTF = "kb:wtf"
    AVATAR_AVATAR = "avatar:avatar"
    # AVATAR_RUSSIA = "avatar:avaru"
    # AVATAR_UKRAINE = "avatar:avauk"
    CONSOLE_TRACEROUTE = "console:traceroute"
    CONSOLE_TCPTRACEROUTE = "console:tcptraceroute"
    CONSOLE_DIG = "console:dig"
    CONSOLE_WHOIS = "console:whois"
    CONSOLE_GEO = "console:geo"
    CVE_CVE = "cve:cve"
    # CVE_ALERT = "cve:alert"
    # CVE_UNALERT = "cve:unalert"
    # CVE_LISTALERTS = "cve:listalerts"
    NAME_GENDER = "name:gender"
    NAME_RACE = "name:race"
    LOGO_TEAM = "logo:team"
    MUSIC_SONG = "music:song"
    MUSIC_ALBUMART = "music:albumart"
    MUSIC_LYRICS = "music:lyrics"
    MUSIC_NOWPLAYING_SONG = "music:nowsong"
    MUSIC_NOWPLAYING_ART = "music:nowart"
    ONTV_TV = "ontv:tv"
    PHOTO_FAKE = "photo:fake"
    HELP = "help"
    FOOTY_STANDINGS = "ft:standings"
    FOOTY_LEAGUES = "ft:leagues"
    FOOTY_FACTS = "ft:facts"
    FOOTY_LINEUP = "ft:lineup"
    FOOTY_SCORES = "ft:games"
    FOOTY_PLAYER = "ft:player"
    FOOTY_STATS = "ft:stats"
    FOOTY_SUBSCRIBE = "ft:subscribe"
    FOOTY_SUBSCRIPTION_UPDATE = "footy_subscription:update"
    FOOTY_UNSUBSCRIBE = "ft:unsubscribe"
    FOOTY_SUBSCRIPTIONS = "ft:listsubscriptions"
    FOOTY_FIXTURES = "ft:fixtures"
    FOOTY_GOALS = "ft:goals"
    FOOTY_LIVE = "ft:live"
    FOOTY_TEAM = "ft:team"
    CHAT_DIALOG = "chat:dialog"
    CHAT_PHRASE = "chat:phrase"
    CHAT_REPLY = "chat:reply"
    TEXT_GENERATE = "text:generate"
    TEXT_DETECT = "text:detect"
    TRANSLATE_EN_ES = "translate:en_es"
    TRANSLATE_ES_EN = "translate:es_en"
    TRANSLATE_EN_BG = "translate:en_bg"
    TRANSLATE_BG_EN = "translate:bg_en"
    TRANSLATE_EN_CS = "translate:en_cs"
    TRANSLATE_CS_EN = "translate:cs_en"
    TRANSLATE_EN_PL = "translate:en_pl"
    TRANSLATE_PL_EN = "translate:pl_en"
    TRANSLATE_SQ_EN = "translate:sq_en"
    TRANSLATE_EN_SQ = "translate:en_sq"
    IMAGE_ANALYZE = "image:analyze"
    IMAGE_GPS2IMG = "image:gps2img"
    IMAGE_TAG = "image:tag"
    IMAGE_HOWCUTE = "image:howcute"
    IMAGE_CLASSIFY = "image:classify"
    IMAGE_PIXEL = "image:pixel"
    IMAGE_POLYGON = "image:polygon"
    IMAGE_WALLPAPER = "image:wallpaper"
    IMAGE_VARIATION = "image:var"
    IMAGE_TXT2IMG = "image:txt2img"
    IMAGE_TXT2PORTRAIT = "image:txt2portrait"
    IMAGE_IMG2IMG = "image:img2img"
    EVENT_COUNTDOWN = "event:countdown"
    EVENT_CALENDAR = "event:calendar"
    EVENT_SCHEDULE = "event:schedule"
    EVENT_CANCEL = "event:cancel"

    # def __eq__(self, __o: object) -> bool:
    #     return self.value == __o.value


class CoreMethods(StrEnum, metaclass=MethodMeta):
    LOGIN = "login"
    HELP = "help"

    # def __eq__(self, __o: object) -> bool:
    #     return self.value == __o.value


Method = TypeVar("Method", ZMethod, CoreMethods)


class ZSONMatcher(StrEnum):
    PHRASE = "phrase"
    SOURCE = "source"


class CommandDef(BaseModel, extra=Extra.ignore):
    method: ZMethod|CoreMethods
    desc: Optional[str] = None
    response: Optional[str] = None
    matcher: Optional[ZSONMatcher] = None
    icon: Optional[str] = None
    subscription: Optional[bool] = Field(default=False)
    args: Optional[str] = None
    upload: Optional[bool] = Field(default=False)

    @property
    def namespace(self) -> str:
        return self.method.value.split(":", 2)[0].strip()

    @property
    def action(self) -> str:
        return self.method.value.split(":")[-1].strip()


class ZSONType(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    PING = "ping"
    PONG = "pong"


class Attachment(BaseModel):
    path: Optional[str] = None
    contentType: Optional[str] = None
    duration: Optional[int] = Field(default=0)
    filename: Optional[str] = None

    def __post_init__(self):
        if self.filename:
            self.path = self.filename
        elif self.path:
            self.filename = Path(self.path).name


NOT_FOUND = [
    "Няма нищо брат",
    "Отиде коня у реката",
    "...and the horse went into the river",
    "Go fish!",
    "Nod fand!",
]

NOT_FOUND_ICONS = [
    ":axe:",
    ":thinking_face:",
    ":open_hands:",
    ":horse_face: :bucket:",
    ":man_walking: :left_arrow:",
]


class RenderResult(BaseModel, extra=Extra.ignore):
    method: Optional[ZMethod|CoreMethods] = None
    message: Optional[str] = Field(default="")
    attachment: Optional[Attachment] = None
    group: Optional[str] = None
    plain: Optional[bool] = Field(default=False)
    error: Optional[str] = None
    new_id: Optional[str] = None


class EmptyResult(RenderResult):

    @property
    def error_message(self):
        try:
            return requests.get(
                "https://commit.cacko.net/index.txt").text.strip()
        except Exception:
            return choice(NOT_FOUND)

    def __post_init__(self):
        self.message = f"{emojize(choice(NOT_FOUND_ICONS))} {self.error_message}"


class ZSONMessage(BaseModel, extra=Extra.ignore):
    ztype: Optional[ZSONType] = None
    id: Optional[str] = None
    client: Optional[str] = None
    group: Optional[str] = None
    method: Optional[ZMethod|CoreMethods] = None
    source: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = uuid4().hex

    def encode(self) -> bytes:
        return self.json().encode()  # type: ignore


class ZSONResponse(ZSONMessage):
    error: Optional[str] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    ztype: ZSONType = Field(default=ZSONType.RESPONSE)
    commands: Optional[list[CommandDef]] = None
    plain: Optional[bool] = False
    new_id: Optional[str] = None

    @property
    def attachment_path(self) -> Optional[Path]:
        if not self.attachment:
            return None
        if not self.attachment.path:
            return None
        res = Path(self.attachment.path)
        return res if res.exists() else None


class ZSONRequest(ZSONMessage):
    source: Optional[str] = None
    lang: Optional[str] = None
    query: Optional[str] = None
    utf8mono: bool = Field(default=True)
    attachment: Optional[Attachment] = None
    ztype: ZSONType = Field(default=ZSONType.REQUEST)


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass

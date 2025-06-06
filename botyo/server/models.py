from uuid import uuid4
from typing import Optional, TypeVar
from corestring import titlecase
from emoji import emojize
from random import choice
from enum import EnumMeta, StrEnum
from pathlib import Path
import sys
import requests
from pydantic import BaseModel, Field
from datetime import datetime


class ApiError(Exception):

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MethodMeta(EnumMeta):
    _enums: dict = {}

    def __new__(metacls, cls, bases, classdict, **kwds):
        for x in classdict._member_names:
            metacls._enums[classdict[x]] = ".".join([classdict["__module__"], cls])
        return super().__new__(metacls, cls, bases, classdict, **kwds)

    def __call__(
        cls, value, names=None, *, module=None, qualname=None, type=None, start=1
    ):
        if names is None:  # simple value lookup
            klass = cls._enums[value]
            papp = Path(".") / "app"
            enumklass = klass.split(".")[-1]
            if enumklass == cls.__name__:
                return cls.__new__(cls, value)  # type: ignore
            if klass.startswith("app."):
                sys.path.insert(0, papp)  # type: ignore
                mod = ".".join(klass.split(".")[:-1])
                imp = __import__(mod, None, None, [enumklass])
                return getattr(imp, enumklass)(value)
            return eval(f'{enumklass}("{value}")')
        return cls._create_(  # type: ignore
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
    # AVATAR_AVATAR = "avatar:avatar"
    # AVATAR_RUSSIA = "avatar:avaru"
    # AVATAR_UKRAINE = "avatar:avauk"
    CONSOLE_TRACEROUTE = "console:traceroute"
    CONSOLE_TCPTRACEROUTE = "console:tcptraceroute"
    CONSOLE_DIG = "console:dig"
    CONSOLE_WHOIS = "console:whois"
    CONSOLE_GEOIP = "console:geoip"
    CONSOLE_GEOCODER = "console:geocoder"
    CODE_GENERAL = "code:general"
    CODE_PHP = "code:php"
    CODE_PYTHON = "code:python"
    CODE_JAVASCRIPT = "code:javascript"
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
    HELP = "help"
    FOOTY_PREDICT = "ft:predict"
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
    FOOTY_H2H = "ft:h2h"
    CHAT_DIALOG = "chat:dialog"
    # CHAT_YOUCOMINGTODAY = "chat:youcomingtoday"
    # CHAT_MINDBLOWINGINNIT = "chat:mingblowinginnit"
    TEXT_GENERATE = "text:generate"
    TEXT_DETECT = "text:detect"
    TEXT_SKILLS = "text:skills"
    TRANSLATE_EN_ES = "translate:en_es"
    TRANSLATE_ES_EN = "translate:es_en"
    TRANSLATE_EN_BG = "translate:en_bg"
    TRANSLATE_BG_EN = "translate:bg_en"
    TRANSLATE_EN_CS = "translate:en_cs"
    TRANSLATE_CS_EN = "translate:cs_en"
    TRANSLATE_EN_PL = "translate:en_pl"
    TRANSLATE_PL_EN = "translate:pl_en"
    TRANSLATE_EN_FR = "translate:en_fr"
    TRANSLATE_FR_EN = "translate:fr_en"
    TRANSLATE_EN_IT = "translate:en_it"
    TRANSLATE_IT_EN = "translate:it_en"    
    IMAGE_STREETVIEW = "image:streetview"
    IMAGE_PIXEL = "image:pixel"
    IMAGE_WALLPAPER = "image:wallpaper"
    IMAGE_VARIATION = "image:var"
    IMAGE_TXT2IMG = "image:txt2img"
    IMAGE_IMG2IMG = "image:img2img"
    IMAGE_QR2IMG = "image:qr2img"
    IMAGE_TXT2QR = "image:txt2qr"
    IMAGE_FACE2IMG = "image:face2img"
    IMAGE_UPLOAD2WALLIES = "image:upload2wallies"
    IMAGE_CLASSIFY = "image:classify"
    IMAGE_DOG = "image:dog"
    IMAGE_IMG2TXT = "image:img2txt"
    EVENT_COUNTDOWN = "event:countdown"
    EVENT_CALENDAR = "event:calendar"
    EVENT_SCHEDULE = "event:schedule"
    EVENT_CANCEL = "event:cancel"
    # MEME_CAPTION = "meme:caption"


class CoreMethods(StrEnum, metaclass=MethodMeta):
    LOGIN = "login"
    HELP = "help"


Method = TypeVar("Method", ZMethod, CoreMethods)


class ZSONMatcher(StrEnum):
    PHRASE = "phrase"
    SOURCE = "source"


class ZSONOption(BaseModel):
    option: str
    choices: list[str]


class CommandDef(BaseModel):
    method: ZMethod | CoreMethods
    desc: Optional[str] = None
    response: Optional[str] = None
    matcher: Optional[ZSONMatcher] = None
    icon: Optional[str] = None
    subscription: bool = Field(default=False)
    args: Optional[str] = None
    upload: bool = Field(default=False)
    uses_prompt: bool = Field(default=False)
    options: Optional[list[ZSONOption]] = None

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
    id: Optional[str] = None
    size: Optional[int] = None

    # def __init__(self, **data):
    #     super().__init__(**data)
    #     if self.filename:
    #         self.path = self.filename
    #     elif self.path:
    #         self.filename = Path(self.path).name


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




class RenderResult(BaseModel):
    method: Optional[ZMethod | CoreMethods] = None
    message: Optional[str] = Field(default="")
    attachment: Optional[Attachment] = None
    group: Optional[str] = None
    plain: Optional[bool] = Field(default=False)
    error: Optional[str] = None
    new_id: Optional[str] = None
    icon: Optional[str] = None
    headline: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None


class EmptyResult(RenderResult):
    @property
    def error_message(self):
        try:
            return requests.get("https://commit.cacko.net/index.txt").text.strip()
        except Exception:
            return choice(NOT_FOUND)

    def __init__(self, **data):
        super().__init__(**data)
        emo = emojize(choice(NOT_FOUND_ICONS))
        self.message = f"{emo} {self.error_message}"


class ErrorResult(EmptyResult):
    @property
    def error_message(self):
        try:
            return requests.get("https://commit.cacko.net/index.txt").text.strip()
        except Exception:
            return choice(NOT_FOUND)

    def __init__(self, **data):
        super().__init__(**data)
        emo = emojize(choice(NOT_FOUND_ICONS))
        if not self.message:
            self.message = f"{self.error_message}"
        self.message = f"{emo} {self.message}\n8======D"


class ZSONMessage(BaseModel):
    ztype: Optional[ZSONType] = None
    id: Optional[str] = None
    client: Optional[str] = None
    group: Optional[str] = None
    method: Optional[ZMethod | CoreMethods] = None
    source: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = uuid4().hex


class ZSONResponse(ZSONMessage):
    error: Optional[str] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    ztype: ZSONType = Field(default=ZSONType.RESPONSE)
    commands: Optional[list[CommandDef]] = None
    plain: bool = Field(default=False)
    new_id: Optional[str] = None
    icon: Optional[str] = None
    headline: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    is_admin: bool = Field(default=False)

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

class Classfier(StrEnum):
    OBJECTS='Classifier'
    AGE='Age'
    GENDER='Gender'
    ATTRACTION='Attraction'
    ETHNIC='Ethnic'
    
class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    
    @property
    def icon(self):
        match self:
            case Gender.MALE:
                return emojize(':male_sign')
            case Gender.FEMALE:
                return emojize(':female_sign:')
            
class Attraction(StrEnum):
    NOT_ATTRACTIVE = "not attractive"
    ATTRACTIVE = "attractive"
    
    @property
    def icon(self):
        match self:
            case Attraction.NOT_ATTRACTIVE:
                return emojize(":thumbs_down:")
            case Attraction.ATTRACTIVE:
                return emojize(':thumbs_up:')

class ClassifyResult(BaseModel):
    label: str
    score: float
    cls: Classfier
    
    @property
    def icon(self):
        match self.cls:
            case Classfier.AGE:
                return f"Age: {self.label} years old"
            case Classfier.GENDER:
                return f"Gender: {self.label} "
            
    def output(self) -> str:
        match self.cls:
            case Classfier.OBJECTS:
                return f"{titlecase(self.label)} {self.score * 100:.2f}%"
            case Classfier.AGE:
                return f"{emojize(':calendar:')} {self.label} years old {self.score * 100:.2f}%"
            case Classfier.GENDER:
                return f"{Gender(self.label).icon} {titlecase(self.label)} {self.score * 100:.2f}%"
            case Classfier.ATTRACTION:
                return f"{Attraction(self.label).icon} {titlecase(self.label)} {self.score * 10:.0f}/10"
            case Classfier.ETHNIC:
                return f"{titlecase(self.label)} {self.score * 100:.2f}%"
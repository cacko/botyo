from os import environ
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from yaml import load, Loader


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OntvConfig:
    api_url: str
    leagues: list[int]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ThreeSixFiveConfig:
    competitions_json: str
    leagues_json: str
    countries_json: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MusicConfig:
    api_url: str
    storage: str
    codec: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DemographicsConfig:
    faggots: Optional[list[str]] = None
    males: Optional[list[str]] = None

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CachableConfig:
    path: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ChatyoConfig:
    base_url: Optional[str]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImageConfig:
    base_url: Optional[str]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GeoConfig:
    base_url: Optional[str]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ApiConfig:
    host: str
    port: int
    daemon_threads: bool
    nworkers: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class BeatsConfig:
    db_url: Optional[str]
    extractor_url: Optional[str]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FavouritesConfig:
    teams: list[int]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GoalsConfig:
    twitter: str
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str
    bearer_token: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    geo: GeoConfig
    ontv: OntvConfig
    music: MusicConfig
    api: ApiConfig
    demographics: DemographicsConfig
    cachable: CachableConfig
    beats: BeatsConfig
    favourites: FavouritesConfig
    threesixfive: ThreeSixFiveConfig
    goals: Optional[GoalsConfig] = None
    chatyo: Optional[ChatyoConfig] = None
    image: Optional[ImageConfig] = None


class ConfigMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    @property
    def geo(cls) -> GeoConfig:
        return cls().struct.geo

    @property
    def beats(cls) -> BeatsConfig:
        return cls().struct.beats

    @property
    def favourites(cls) -> FavouritesConfig:
        return cls().struct.favourites

    @property
    def api(cls) -> ApiConfig:
        return cls().struct.api

    @property
    def ontv(cls) -> OntvConfig:
        return cls().struct.ontv

    @property
    def music(cls) -> MusicConfig:
        return cls().struct.music

    @property
    def demographics(cls) -> DemographicsConfig:
        return cls().struct.demographics

    @property
    def cachable(cls) -> CachableConfig:
        return cls().struct.cachable

    @property
    def threesixfive(cls) -> ThreeSixFiveConfig:
        return cls().struct.threesixfive

    @property
    def chatyo(cls) -> ChatyoConfig:
        return cls().struct.chatyo

    @property
    def image(cls) -> ImageConfig:
        return cls().struct.image

    @property
    def goals(cls) -> GoalsConfig:
        return cls().struct.goals


class Config(object, metaclass=ConfigMeta):

    struct: ConfigStruct

    def __init__(self):

        settings = Path(
            environ.get("SETTINGS_PATH", Path(__file__).parent.parent / "settings.yaml")
        )
        data = load(settings.read_text(), Loader=Loader)
        self.struct = ConfigStruct.from_dict(data)  # type: ignore

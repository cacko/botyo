from os import environ
from pathlib import Path
from typing import Optional
from yaml import load, Loader
from pydantic import BaseModel, Extra, Field


class OntvConfig(BaseModel, extra=Extra.ignore):
    api_url: str
    leagues: list[int]


class ThreeSixFiveConfig(BaseModel, extra=Extra.ignore):
    competitions_json: str
    leagues_json: str
    countries_json: str


class MusicConfig(BaseModel, extra=Extra.ignore):
    api_url: str
    storage: str
    codec: str


class DemographicsConfig(BaseModel, extra=Extra.ignore):
    faggots: Optional[list[str]] = None
    males: Optional[list[str]] = None


class CachableConfig(BaseModel, extra=Extra.ignore):
    path: str


class ChatyoConfig(BaseModel, extra=Extra.ignore):
    base_url: Optional[str]


class ImageConfig(BaseModel, extra=Extra.ignore):
    base_url: Optional[str]


class GeoConfig(BaseModel, extra=Extra.ignore):
    base_url: Optional[str]


class ApiConfig(BaseModel, extra=Extra.ignore):
    host: str
    port: int
    daemon_threads: bool
    nworkers: int


class BeatsConfig(BaseModel, extra=Extra.ignore):
    db_url: Optional[str]
    extractor_url: Optional[str]


class FavouritesConfig(BaseModel, extra=Extra.ignore):
    teams: list[int]


class GoalsConfig(BaseModel, extra=Extra.ignore):
    twitter: str
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str
    bearer_token: str


class S3Config(BaseModel):
    aws_cloudfront_host: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_region: str
    aws_storage_bucket_name: str
    aws_directory: str


class ConfigStruct(BaseModel, extra=Extra.ignore):
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
    s3: Optional[S3Config] = None


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

    @property
    def s3(cls) -> S3Config:
        return cls().struct.s3


class Config(object, metaclass=ConfigMeta):

    struct: ConfigStruct

    def __init__(self):

        settings = Path(
            environ.get("SETTINGS_PATH", Path(__file__).parent.parent / "settings.yaml")
        )
        data = load(settings.read_text(), Loader=Loader)
        self.struct = ConfigStruct(**data)  # type: ignore

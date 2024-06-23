from os import environ
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel


class OntvConfig(BaseModel):
    api_url: str
    leagues: list[int]


class ThreeSixFiveConfig(BaseModel):
    competitions_json: str
    leagues_json: str
    countries_json: str


class MusicConfig(BaseModel):
    api_url: str
    storage: str
    codec: str
    beets_config: str


class DemographicsConfig(BaseModel):
    faggots: list[str]
    males: list[str]


class CachableConfig(BaseModel):
    path: str


class ChatyoConfig(BaseModel):
    base_url: Optional[str]


class ImageConfig(BaseModel):
    base_url: Optional[str]


class GeoConfig(BaseModel):
    base_url: Optional[str]


class ApiConfig(BaseModel):
    host: str
    port: int
    daemon_threads: bool
    nworkers: int


class BeatsConfig(BaseModel):
    db_url: Optional[str]
    extractor_url: Optional[str]
    store_root: str


class PredictConfig(BaseModel):
    db_url: str

class FavouritesConfig(BaseModel):
    teams: list[int]


class GoalsConfig(BaseModel):
    twitter: str
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str
    bearer_token: str


class S3Config(BaseModel):
    cloudfront_host: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    storage_bucket_name: str
    directory: str


class ImgFlipConfig(BaseModel):
    username: str
    password: str


class SuperUserRule(BaseModel):
    startswith: str
    endswith: Optional[str] = None

    def evaluate(self, source: str) -> bool:
        return all([
            source.startswith(self.startswith),
            source.endswith(self.endswith) if self.endswith else True
        ])


class SuperUser(BaseModel):
    signal: SuperUserRule
    whatsapp: SuperUserRule
    botyo: SuperUserRule

    def evaluate(self, source) -> Optional[str]:
        if self.signal.evaluate(source):
            return "signal"
        if self.whatsapp.evaluate(f"{source}"):
            return "whatsapp"
        if self.botyo.evaluate(source):
            return "botyo"
        return None


class UsersConfig(BaseModel):
    admin: list[str]
    superuser: SuperUser


class LametricConfig(BaseModel):
    host: str
    secret: str

class ConfigStruct(BaseModel):
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
    imgflip: Optional[ImgFlipConfig] = None
    users: UsersConfig
    lametric: LametricConfig
    predict: PredictConfig


config_root = Path(
    environ.get("SETTINGS_PATH", Path(__file__).parent.parent / "settings.yaml")
)
data = yaml.full_load(Path(config_root).read_text())
Config = ConfigStruct(**data)
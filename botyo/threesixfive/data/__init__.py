import json
from pathlib import Path
from botyo.core.config import Config
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from typing import Optional

COUNTRY_ID_INTERNATIONAL = 54


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CountryItem:
    id: int
    name: str
    totalGames: Optional[int] = None
    liveGames: Optional[int] = None
    nameForURL: Optional[str] = None
    sportTypes: Optional[list[int]] = None

    @property
    def is_international(self) -> bool:
        return self.id == COUNTRY_ID_INTERNATIONAL


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LeagueItem:
    id: int
    league_id: int
    league_name: str
    country_id: int
    country_name: str
    sport_id: int
    sport_name: str

    @property
    def is_international(self) -> bool:
        return self.country_id == COUNTRY_ID_INTERNATIONAL


class Data365Meta(type):
    _instance = None
    _leagues = []
    _countries = []

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    @property
    def countries(cls) -> list[CountryItem]:
        if not cls._countries:
            cls._countries = cls().getCountries()
        return cls._countries

    @property
    def leagues(cls) -> list[LeagueItem]:
        if not cls._leagues:
            cls._leagues = cls().getLeagues()
        return cls._leagues


class Data365(object, metaclass=Data365Meta):
    def getCompetitionsPath(self) -> Path:
        return Path(__file__).parent / Config.threesixfive.competitions_json

    def getCountriesPath(self) -> Path:
        return Path(__file__).parent / Config.threesixfive.countries_json

    def getLeaguesPath(self) -> Path:
        p = Path(__file__).parent / Config.threesixfive.leagues_json
        if not p.exists():
            competitions_path = self.getCompetitionsPath()
            competitions = json.loads(competitions_path.read_text())
            countries = {c.get("id"): c for c in competitions.get("countries")}
            sports = {s.get("id"): s for s in competitions.get("sports")}
            txt = json.dumps(
                [
                    {
                        "id": comp.get("id"),
                        "league_id": comp.get("id"),
                        "league_name": comp.get("name"),
                        "country_id": comp.get("countryId"),
                        "country_name": countries[comp.get("countryId")].get(
                            "name"
                        ),
                        "sport_id": comp.get("sportId"),
                        "sport_name": sports[comp.get("sportId")].get("name"),
                    }
                    for comp in competitions.get("competitions")
                ]
            )
            p.write_text(txt)
        return p

    def getCountries(self) -> list[CountryItem]:
        countries_path = self.getCountriesPath()
        data = json.loads(countries_path.read_text())
        countries_json = json.dumps(data.get("countries"))
        return CountryItem.schema().loads(  # type: ignore
            countries_json, many=True
        )

    def getLeagues(self) -> list[LeagueItem]:
        leagues_path = self.getLeaguesPath()
        return LeagueItem.schema().loads(  # type: ignore
            leagues_path.read_text(), many=True
        )

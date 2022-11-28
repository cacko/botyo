import json
from pathlib import Path
from app.core.config import Config
from app.threesixfive.item.models import CountryItem, LeagueItem


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

    def getLeaguesPath(self) -> Path:
        p = Path(__file__).parent / Config.threesixfive.leagues_json
        if not p.exists():
            competitions_path = self.getCompetitionsPath()
            competitions = json.loads(competitions_path.read_text())
            countries = {c.get("id"): c for c in competitions.get("countries")}
            sports = {s.get("id"): s for s in competitions.get("sports")}
            p.write_text(json.dumps([{
                "id": comp.get("id"),
                "league_id": comp.get("id"),
                "league_name": comp.get("name"),
                "country_id": comp.get("countryId"),
                "country_name": countries[comp.get("countryId")].get("name"),
                "sport_id": comp.get("sportId"),
                "sport_name": sports[comp.get("sportId")].get("name"),
            } for comp in competitions.get("competitions")]
            ))
        return p

    def getCountries(self) -> list[CountryItem]:
        competitions_path = self.getCompetitionsPath()
        competitions = json.loads(competitions_path.read_text())
        countries_json = json.dumps(competitions.get("countries"))
        return CountryItem.schema().loads(countries_json, many=True)  # type: ignore

    def getLeagues(self) -> list[LeagueItem]:
        leagues_path = self.getLeaguesPath()
        return LeagueItem.schema().loads(leagues_path.read_text(), many=True)  # type: ignore

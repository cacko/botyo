from enum import Enum
from datetime import datetime
from urllib.parse import urlencode
from pydantic import BaseModel, Field


class BASEURL(Enum):
    ALLSCORES = "https://webws.365scores.com/web/games/allscores"
    LIVESCORES = "https://webws.365scores.com/web/games/current"
    H2H = "https://webws.365scores.com/web/games/h2h"
    GAME = "https://webws.365scores.com/web/game"
    COMPETITIONS = "https://webws.365scores.com/web/competitions"
    COMPETITION_IMAGE = (
        "https://imagecache.365scores.com/image/upload/"
        "f_png,w_24,h_24,c_limit,q_auto:eco,dpr_2,d_Countries:Round:17.png/v2/"
        "Competitions/"
    )
    TEAM_IMAGE = (
        "https://imagecache.365scores.com/image/upload/"
        "f_png,w_200,h_200,c_limit,q_auto:eco,dpr_3,"
        "d_Competitors:default1.png/v3/Competitors"
    )
    STANDINGS = "https://webws.365scores.com/web/standings"
    BRACKETS = "https://webws.365scores.com/web/brackets"
    SEARCH = "https://webws.365scores.com/web/search/"
    TEAM_STATS = "https://webws.365scores.com/web/stats/"
    COMPETITION_SCHEDULE = "https://webws.365scores.com/web/games/current"


class CompetitionScheduleArguments(BaseModel):
    competitions: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    showOdds: bool = Field(default=True)


class StandingsArguments(BaseModel):
    competitions: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    showOdds: bool = Field(default=True)
    live: bool = Field(default=True)


class BracketsArguments(BaseModel):
    competitions: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    showOdds: bool = Field(default=True)
    live: bool = Field(default=True)


class SearchArguments(BaseModel):
    query: str
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    filter: str = "all"


class TeamStatsArguments(BaseModel):
    competitor: int
    competition: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    filter: str = Field(default="all")


class LiveScoresArguments(BaseModel):
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    showOdds: bool = Field(default=True)
    competitions: str = Field(default="")


class CompetitorScoresArguments(BaseModel):
    competitors: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    showOdds: bool = Field(default=True)


class AllScoresArguments(BaseModel):
    startDate: str = Field(default="")
    endDate: str = Field(default="")
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    sports: int = Field(default=1)
    showOdds: bool = Field(default=True)
    onlyMajorGames: bool = Field(default=False)
    withTop: bool = Field(default=True)

    def __init__(self, **data):
        super().__init__(**data)
        now = datetime.now().strftime("%d/%m/%y")
        self.startDate = now
        self.endDate = now


class GameArguments(BaseModel):
    gameId: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)


class H2HArguments(BaseModel):
    gameId: int
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)



class CompetitionsArguments(BaseModel):
    appTypeId: int = Field(default=5)
    langId: int = Field(default=1)
    timezoneName: str = Field(default="UTC")
    userCountryId: int = Field(default=1)
    sportId: int = Field(default=1)


class UrlMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UrlMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def search(cls, filter: str):
        query = SearchArguments(query=filter)
        return f"{BASEURL.SEARCH.value}/?{urlencode(query.model_dump())}"

    def livescores(cls, leagues):
        if not leagues:
            query = AllScoresArguments()
            return f"{BASEURL.ALLSCORES.value}/?{urlencode(query.model_dump())}"
        query = LiveScoresArguments(competitions=",".join(map(str, leagues)))
        return f"{BASEURL.LIVESCORES.value}/?{urlencode(query.model_dump())}"

    def badge(cls, team_id):
        return f"{BASEURL.TEAM_IMAGE.value}/{team_id}"

    def game(cls, game_id):
        query = GameArguments(gameId=game_id)
        return f"{BASEURL.GAME.value}/?{urlencode(query.model_dump())}"
    
    def h2h(cls, game_id):
        query = H2HArguments(gameId=game_id)
        return f"{BASEURL.H2H.value}/?{urlencode(query.model_dump())}"

    def competitions(cls):
        query = CompetitionsArguments()
        return f"{BASEURL.COMPETITIONS.value}/?{urlencode(query.model_dump())}"

    def competition_logo(cls, competition_id):
        return f"{BASEURL.COMPETITION_IMAGE.value}/{competition_id}"

    def competition_schedule(cls, competition_id):
        query = CompetitionScheduleArguments(competitions=competition_id)
        return f"{BASEURL.COMPETITION_SCHEDULE.value}/?{urlencode(query.model_dump())}"

    def standings(cls, competition_id):
        query = StandingsArguments(competitions=competition_id)
        return f"{BASEURL.STANDINGS.value}/?{urlencode(query.model_dump())}"

    def brackets(cls, competition_id):
        query = BracketsArguments(competitions=competition_id)
        return f"{BASEURL.BRACKETS.value}/?{urlencode(query.model_dump())}"

    def team_games(cls, competitor_id):
        query = CompetitorScoresArguments(competitors=competitor_id)
        return f"{BASEURL.LIVESCORES.value}/?{urlencode(query.model_dump())}"


class Url(metaclass=UrlMeta):
    pass

from enum import Enum
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode


class BASEURL(Enum):
    ALLSCORES = "https://webws.365scores.com/web/games/allscores"
    LIVESCORES = "https://webws.365scores.com/web/games/current"
    GAME = "https://webws.365scores.com/web/game"
    COMPETITIONS = "https://webws.365scores.com/web/competitions"
    COMPETITION_IMAGE = (
        "https://imagecache.365scores.com/image/upload/"
        "f_png,w_24,h_24,c_limit,q_auto:eco,dpr_2,d_Countries:Round:17.png/v2/Competitions/"
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


@dataclass_json
@dataclass
class CompetitionScheduleArguments:
    competitions: int
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    showOdds: bool = True


@dataclass_json
@dataclass
class StandingsArguments:
    competitions: int
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    showOdds: bool = True
    live: bool = True


@dataclass_json
@dataclass
class BracketsArguments:
    competitions: int
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    showOdds: bool = True
    live: bool = True


@dataclass_json
@dataclass
class SearchArguments:
    query: str
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    filter: str = "all"


@dataclass_json
@dataclass
class TeamStatsArguments:
    competitor: int
    competition: int
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    filter: str = "all"


@dataclass_json
@dataclass
class LiveScoresArguments:
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    showOdds: bool = True
    competitions: str = ""


@dataclass_json
@dataclass
class CompetitorScoresArguments:
    competitors: int
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    showOdds: bool = True


@dataclass_json
@dataclass
class AllScoresArguments:
    startDate: str = ""
    endDate: str = ""
    appTypeId: int = 5
    langId: int = 1
    timezoneName: str = "UTC"
    userCountryId: int = 1
    sports: int = 1
    showOdds: bool = True
    onlyMajorGames: bool = False
    withTop: bool = True

    def __post_init__(self):
        now = datetime.now().strftime("%d/%m/%y")
        self.startDate = now
        self.endDate = now


@dataclass_json
@dataclass
class GameArguments:
    gameId: int
    appTypeId: int = 5
    langId: int = 10
    timezoneName: str = "UTC"
    userCountryId: int = 1


@dataclass_json
@dataclass
class CompetitionsArguments:
    appTypeId: int = 5
    langId: int = 10
    timezoneName: str = "UTC"
    userCountryId: int = 1
    sportId: int = 1


class UrlMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UrlMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def search(cls, filter: str):
        query = SearchArguments(query=filter)
        return f"{BASEURL.SEARCH.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def livescores(cls, leagues):
        if not leagues:
            query = AllScoresArguments()
            return f"{BASEURL.ALLSCORES.value}/?{urlencode(query.to_dict())}"  # type: ignore
        query = LiveScoresArguments(competitions=",".join(map(str, leagues)))
        return f"{BASEURL.LIVESCORES.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def badge(cls, team_id):
        return f"{BASEURL.TEAM_IMAGE.value}/{team_id}"

    def game(cls, game_id):
        query = GameArguments(gameId=game_id)
        return f"{BASEURL.GAME.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def competitions(cls):
        query = CompetitionsArguments()
        return f"{BASEURL.COMPETITIONS.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def competition_logo(cls, competition_id):
        return f"{BASEURL.COMPETITION_IMAGE.value}/{competition_id}"

    def competition_schedule(cls, competition_id):
        query = CompetitionScheduleArguments(competitions=competition_id)
        return f"{BASEURL.COMPETITION_SCHEDULE.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def standings(cls, competition_id):
        query = StandingsArguments(competitions=competition_id)
        return f"{BASEURL.STANDINGS.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def brackets(cls, competition_id):
        query = BracketsArguments(competitions=competition_id)
        return f"{BASEURL.BRACKETS.value}/?{urlencode(query.to_dict())}"  # type: ignore

    def team_games(cls, competitor_id):
        query = CompetitorScoresArguments(competitors=competitor_id)
        return f"{BASEURL.LIVESCORES.value}/?{urlencode(query.to_dict())}"  # type: ignore


class Url(metaclass=UrlMeta):
    pass

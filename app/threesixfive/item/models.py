from asyncio.log import logger
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from dataclasses_json import CatchAll, dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum
from string import punctuation
import re
from zoneinfo import ZoneInfo
from app.core.time import time_hhmm
from stringcase import constcase
from hashlib import md5
from app.core.config import Config as app_config
from emoji import emojize

class EventStatus(Enum):
    HT = "HT"
    FT = "FT"
    PPD = "PPD"
    CNL = "CNL"
    AET = "AET"
    NS = "NS"


STATUS_MAP = {
    "Post.": "PPD",
    "Ended": "FT",
    "Canc.": "CNL",
    "Sched.": "NS",
    "Just Ended": "FT",
    "After ET": "AET",
    "After Pen": "AET",
    "Half Time": "HT",
    "2nd Half": '2nd'
}


class GameStatus(Enum):
    FT = "Ended"
    JE = "Just Ended"
    SUS = "Susp"
    ABD = "Aband."
    AET = "After Pen"
    NS = "NS"
    FN = "Final"
    PPD = "Post."
    CNL = "Canc."
    HT = "Half Time"
    _2ND = "2nd"

class OrderWeight(Enum):
    INPLAY = 1
    HT = pow(2, 1)
    LIVE = pow(2, 1)
    FT = pow(2, 2)
    EAT = pow(2, 3)
    ET = pow(2, 3)
    NS = pow(2, 3)
    PPD = pow(2, 4)
    JUNK = pow(2, 5)


class LineupMemberStatus(IntEnum):
    STARTING = 1
    SUBSTITUTE = 2
    MISSING = 3
    MANAGEMENT = 4
    DOUBTHFUL = 5


class ActionIcon(Enum):
    SUBSTITUTION = ":ON!_arrow:"
    GOAL = ":soccer_ball:"
    YELLOW__CARD = ":yellow_square:"
    RED__CARD = ":red_square:"
    WOODWORK = ":palm_tree:"
    PENALTY__MISS = ":cross_mark:"
    GOAL__DISALLOWED = ":double_exclamation_mark:"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CountryItem:
    id: int
    name: str
    totalGames: Optional[int] = None
    liveGames: Optional[int] = None
    nameForURL: Optional[str] = None
    sportTypes: Optional[list[int]] = None


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


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Event:
    id: str
    idEvent: int
    strSport: str
    idLeague: int
    strLeague: str
    idHomeTeam: int
    idAwayTeam: int
    strHomeTeam: str
    strAwayTeam: str
    strStatus: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso", tzinfo=timezone.utc),
        )
    )
    intHomeScore: Optional[int] = -1
    intAwayScore: Optional[int] = -1
    sort: int = 0
    details: Optional[str] = None
    displayScore: Optional[str] = ""
    displayStatus: Optional[str] = ""
    source: Optional[str] = ""
    strWinDescription: Optional[str] = ""

    def __post_init__(self):
        if self.strStatus in STATUS_MAP:
            self.strStatus = STATUS_MAP[self.strStatus]

        delta = (datetime.now(timezone.utc) -
                 self.startTime).total_seconds() / 60
        try:
            self.displayStatus = GameStatus(self.strStatus)
            if delta < 0 and self.displayStatus in [GameStatus.NS]:
                self.displayStatus = self.startTime.astimezone(
                    ZoneInfo("Europe/London")).strftime("%H:%M")
            else:
                self.displayStatus = self.displayStatus.value
        except Exception:
            self.displayStatus = self.strStatus
        try:
            if re.match(r"^\d+", self.strStatus):
                self.sort = OrderWeight.INPLAY.value * int(self.strStatus)
                self.displayStatus = f"{self.strStatus}\""
            else:
                self.sort = OrderWeight[
                    self.strStatus.translate(punctuation).upper()
                ].value * abs(delta)
        except KeyError as e:
            self.sort = OrderWeight.JUNK.value * abs(delta)
        if any([self.intAwayScore == -1, self.intHomeScore == -1]):
            self.displayScore = ""
        else:
            self.displayScore = ":".join([
                f"{self.intHomeScore:.0f}",
                f"{self.intAwayScore:.0f}"
            ])

    @property
    def inProgress(self) -> bool:
        return re.match(r"^\d+$", self.strStatus)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Sport:
    id: int
    name: str
    nameForURL: str
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Country:
    id: int
    name: str
    nameForURL: int
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Competitor:
    id: int
    countryId: int
    sportId: int
    name: str
    nameForURL: str
    type: int
    color: str
    mainCompetitionId: int
    popularityRank: Optional[int] = None
    symbolicName: Optional[str] = None
    imageVersion: Optional[int] = None

@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class StandingRow:
    competitor: Competitor
    gamePlayed: Optional[int] = None
    gamesWon: Optional[int] = None
    gamesLost: Optional[int] = None
    gamesEven: Optional[int] = None
    forward: Optional[int] = None
    against: Optional[int] = None
    ratio: Optional[int] = None
    points: Optional[int] = None
    strike: Optional[int] = None
    gamesOT: Optional[int] = None
    gamesWonOnOT: Optional[int] = None
    gamesWonOnPen: Optional[int] = None
    gamesLossOnOT: Optional[int] = None
    gamesLossOnPen: Optional[int] = None
    groupNum: Optional[int] = None
    pct: Optional[str] = None
    position: Optional[int] = None
    unknown: Optional[CatchAll] = None

    def __post_init__(self):
        self.forward = self.unknown.get("for")


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Standing:
    competitionId: int
    seasonNum: Optional[int] = None
    stageNum: Optional[int] = None
    isCurrentStage: Optional[bool] = None
    displayName: Optional[str] = None
    currentGroupCategory: Optional[int] = None
    rows: Optional[list[StandingRow]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class StandingResponse:
    lastUpdateId: int
    requestedUpdateId: int
    ttl: int
    standings: list[Standing]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Competition:
    id: int
    countryId: int
    sportId: int
    name: str
    nameForURL: Optional[str] = False
    popularityRank: Optional[int] = False
    color: Optional[str] = False
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0
    hasActiveGames: Optional[bool] = False
    hasStandings: Optional[bool] = False
    hasBrackets: Optional[bool] = False

    @property
    def flag(self) -> str:
        pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameMember:
    competitorId: Optional[int] = None
    name: Optional[str] = None
    id: Optional[int] = None
    shortName: Optional[str] = None
    nameForURL: Optional[str] = None
    imageVersion: Optional[int] = 0
    athleteId: Optional[int] = 0
    jerseyNumber: Optional[int] = 0

    @property
    def displayName(self) -> str:
        return self.shortName if self.shortName else self.name


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LineupPosition:
    id: int
    name: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MemberStat:
    value: str
    name: str
    shortName: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LineupMember:
    id: int
    status: LineupMemberStatus
    statusText: str
    position: Optional[LineupPosition] = None
    stats: Optional[list[MemberStat]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Lineup:
    status: Optional[str] = None
    formation: Optional[str] = None
    hasFieldPositions: Optional[bool] = False
    members: Optional[list[LineupMember]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameStatistic:
    id: int
    name: str
    categoryId: int
    categoryName: str
    value: str
    isMajor: Optional[bool]
    valuePercentage: Optional[int]
    isPrimary: Optional[bool]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameCompetitor:
    id: Optional[int] = None
    countryId: Optional[int] = None
    sportId: Optional[int] = None
    name: Optional[str] = None
    score: Optional[int] = None
    isQualified: Optional[bool] = None
    toQualify: Optional[bool] = None
    isWinner: Optional[bool] = None
    type: Optional[int] = None
    imageVersion: Optional[int] = None
    mainCompetitionId: Optional[int] = None
    redCards: Optional[int] = None
    popularityRank: Optional[int] = None
    lineups: Optional[Lineup] = None
    statistics: Optional[list[GameStatistic]] = None
    symbolicName: Optional[str] = None

    def __getattribute__(self, __name: str):
        if __name == "name" and object.__getattribute__(self, "id") in app_config.favourites.teams:
            return f"{object.__getattribute__(self, __name).upper()}"
        return object.__getattribute__(self, __name)

    @property
    def flag(self) -> str:
        pass

    @property
    def shortName(self) -> str:
        if self.symbolicName:
            return self.symbolicName
        parts = self.name.split(' ')
        if len(parts) == 1:
            return self.name[:3].upper()
        return f"{parts[0][:1]}{parts[1][:2]}".upper()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OddsRate:
    decimal: Optional[float] = None
    fractional: Optional[str] = None
    american: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OddsOptions:
    num: int
    rate: OddsRate


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Odds:
    lineId: int
    gameId: int
    bookmakerId: int
    lineTypeId: int
    options: list[OddsOptions]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameFact:
    id: str
    text: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Game:
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    statusGroup: int
    statusText: str
    shortStatusText: str
    gameTimeAndStatusDisplayType: int
    gameTime: int
    gameTimeDisplay: str
    homeCompetitor: GameCompetitor
    awayCompetitor: GameCompetitor
    odds: Optional[Odds] = None
    roundName: Optional[str] = ""
    roundNum: Optional[int] = None
    seasonNum: Optional[int] = 0
    stageNum: Optional[int] = 0
    justEnded: Optional[bool] = None
    hasLineups: Optional[bool] = None
    hasMissingPlayers: Optional[bool] = None
    hasFieldPositions: Optional[bool] = None
    hasTVNetworks: Optional[bool] = None
    hasBetsTeaser: Optional[bool] = None
    matchFacts: Optional[list[GameFact]] = None
    winDescription: Optional[str] = ""
    aggregateText: Optional[str] = ""
    icon: Optional[str] = ""

    @property
    def round(self) -> str:
        if self.roundNum is None:
            return ""
        ' '.join(
            list(filter(lambda x: x, [f"{self.roundName}", f"{self.roundNum:,0f}"])))

    @property
    def postponed(self) -> bool:
        try:
            status = GameStatus(self.shortStatusText)
            return status == GameStatus.PPD
        except ValueError:
            return False

    @property
    def canceled(self) -> bool:
        try:
            status = GameStatus(self.shortStatusText)
            return status == GameStatus.CNL
        except ValueError:
            return False

    @property
    def not_started(self) -> bool:
        res = self.startTime > datetime.now(tz=timezone.utc)
        return res

    @property
    def ended(self) -> bool:
        if self.not_started:
            return False
        status = self.shortStatusText
        try:
            _status = GameStatus(status)
            if _status in (GameStatus.FT, GameStatus.AET, GameStatus.PPD):
                return True
            return _status == GameStatus.HT or re.match(r"^\d+$", status)
        except ValueError:
            return False

    @property
    def displayStatus(self) -> str:
        zone = ZoneInfo("Europe/London")
        if self.not_started:
            return f"{time_hhmm(self.startTime,zone)}"
        status = GameStatus(self.shortStatusText)
        if self.ended:
            return self.displayScore
        if status == GameStatus.HT:
            return "HT"
        return self.gameTimeDisplay

    @property
    def displayScore(self) -> str:
        return f"{max(self.homeCompetitor.score, 0):.0f}:{max(self.awayCompetitor.score, 0):.0f}"

    @property
    def displayTitle(self) -> str:
        res = f"{self.homeCompetitor.name} - {self.awayCompetitor.name}"
        if all([not self.not_started, not self.ended]):
            res = f"{res} {self.displayScore}"
        return res

class EVENT_ICON(Enum):
    SUBSTITUTION = ":ON!_arrow:"
    GOAL = ":soccer_ball:"
    YELLOW__CARD = ":yellow_square:"
    RED__CARD = ":red_square:"
    WOODWORK = ":palm_tree:"
    PENALTY__MISS = ":cross_mark:"
    GOAL__DISALLOWED = ":double_exclamation_mark:"


class EVENT_NAME(Enum):
    PENALTY_MISS = "Penalty Miss"
    YELLOW_CARD = "Yellow Card"
    RED_CARD = "Red Card"
    WOODWORK = "Woodwork"
    GOAL_DISALLOWED = "Goal Disallowed"
    GOAL = "Goal"
    SUBSTITUTION = "Substitution"
    UNKNOWN = "IUnknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class EVENT_SUBTYPE_NAME(Enum):
    PENALTY = "Penalty"
    UNKNOWN = "IUnknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameEventType:
    id: Optional[int] = None
    name: Optional[str] = None
    subTypeId: Optional[int] = None
    subTypeName: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameEvent:
    competitorId: Optional[int] = 0
    eventType: Optional[GameEventType] = None
    statusId: Optional[int] = 0
    stageId: Optional[int] = 0
    order: Optional[int] = 0
    num: Optional[int] = 0
    gameTime: Optional[int] = 0
    addedTime: Optional[int] = 0
    gameTimeDisplay: Optional[str] = None
    gameTimeAndStatusDisplayType: Optional[int] = 0
    playerId: Optional[int] = 0
    isMajor: Optional[bool] = False
    extraPlayers: Optional[list[int]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameDetails(Game):
    events: Optional[list[GameEvent]] = None
    members: Optional[list[GameMember]] = None
    homeCompetitor: Optional[GameCompetitor] = None
    awayCompetitor: Optional[GameCompetitor] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ResponseGame:
    lastUpdateId: int
    requestedUpdateId: int
    game: GameDetails

    @property
    def events(self) -> list[Event]:
        if not self.game:
            return []
        if not self.game.events:
            return []
        return self.game.events

    @property
    def status(self) -> str:
        if not self.game:
            return None
        return self.game.shortStatusText


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ResponseScores:
    lastUpdateId: int
    requestedUpdateId: int
    ttl: int
    sports: list[Sport]
    countries: list[Country]
    competitions: list[Competition]
    competitors: list[Competitor]
    games: list[Game]
    liveGamesCount: Optional[int] = None


class Position(IntEnum):
    HOME = 1
    AWAY = 2
    NONE = 3


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DetailsEvent:
    time: str
    action: str
    order: Optional[int] = 0
    team: Optional[str] = None 
    player: Optional[str] = None
    extraPlayers: Optional[str] = None
    position: Optional[Position] = None
    score: Optional[str] = None

    @property
    def displayTime(self) -> str:
        return f'{self.time:3.0f}"'

    @property
    def icon(self) -> str:
        try:
            id = constcase(self.action)
            icon = EVENT_ICON[id]
            return emojize(icon.value)
        except ValueError:
            return ""



@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DetailsEventPixel:
    event_id: int
    time: int
    action: str
    is_old_event: bool
    order: Optional[int] = 0
    team: Optional[str] = None
    player: Optional[str] = None
    extraPlayers: Optional[str] = None
    score: Optional[str] = None
    team_id: Optional[int] = None
    event_name: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self) -> None:
        logger.warning(f"{self.event_name}")
        self.id = md5(f"{self.event_name}".lower().encode()).hexdigest()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SubscriptionEvent:
    start_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    action: str
    league: str
    league_id: int
    home_team: str
    home_team_id: int
    away_team: str
    away_team_id: int
    event_id: int
    event_name: str
    job_id: str
    icon: str
    status: Optional[str] = ""
    id: Optional[str] = None

    def __post_init__(self) -> None:
        self.id = md5(f"{self.home_team}/{self.away_team}".lower().encode()).hexdigest()

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CancelJobEvent:
    job_id: str
    action: str = 'Cancel Job'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SearchResponse:
    competitors: Optional[list[Competitor]] = None
    competitions: Optional[list[Competition]] = None

    @property
    def results(self) -> list[Competitor]:
        if not self.competitors:
            return []
        return list(filter(lambda x: x.sportId == 1, self.competitors))

    @property
    def results_competitions(self) -> list[Competition]:
        if not self.competitions:
            return []
        return list(filter(lambda x: x.sportId == 1, self.competitions))


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CompetitionResponse:
    sports: list[Sport]
    countries: list[Country]
    competitions: list[Competition]
    games: list[Game]
    competitors: Optional[list[Competitor]] = None

class OddLineType:
    id: int
    name: str #"Full Time Result"
    shortName: str #"1X2"
    title: str #"Full Time Result"

class OddBoomaker:
    id: int #14,
    name: str #Bet365",
    link: str #https://www.bet365.com/olp/open-account/?affiliate=365_178380",
    nameForURL: str #bet365",
    color: str ##007B5B",
    imageVersion: int #1

# @dataclass_json(undefined=Undefined.EXCLUDE)
# @dataclass
# class Odds:
#     lineId: int #366367380,
#     gameId: int #3623949,
#     bookmakerId: int #14,
#     lineTypeId: int #1,
#     lineType: OddLineType
#     bookmaker: OddBoomaker
#     "options": [
#           {
#             "num": 1,
#             "rate": {
#               "decimal": 1.12,
#               "fractional": "1/8",
#               "american": "-833"
#             },
#             "oldRate": {
#               "decimal": 1.11,
#               "fractional": "1/9",
#               "american": "-909"
#             },
#             "prematchRate": {
#               "decimal": 2.15,
#               "fractional": "7/6",
#               "american": "+115"
#             },
#             "link": "https://www.bet365.com/olp/open-account/?affiliate=365_178380",
#             "trend": 3
#           },
#           {
#             "num": 2,
#             "rate": {
#               "decimal": 7.5,
#               "fractional": "13/2",
#               "american": "+650"
#             },
#             "oldRate": {
#               "decimal": 7,
#               "fractional": "6/1",
#               "american": "+600"
#             },
#             "prematchRate": {
#               "decimal": 3.8,
#               "fractional": "14/5",
#               "american": "+280"
#             },
#             "link": "https://www.bet365.com/olp/open-account/?affiliate=365_178380",
#             "trend": 3
#           },
#           {
#             "num": 3,
#             "rate": {
#               "decimal": 15,
#               "fractional": "14/1",
#               "american": "+1400"
#             },
#             "oldRate": {
#               "decimal": 17,
#               "fractional": "16/1",
#               "american": "+1600"
#             },
#             "prematchRate": {
#               "decimal": 2.75,
#               "fractional": "7/4",
#               "american": "+175"
#             },
#             "link": "https://www.bet365.com/olp/open-account/?affiliate=365_178380",
#             "trend": 1
#           }
#         ]
#       },
#       "isHomeAwayInverted": false,
#       "hasStandings": true,
#       "standingsName": "Table",
#       "hasBrackets": false,
#       "hasPreviousMeetings": false
import logging
from typing import Optional, Any
from datetime import datetime, timezone
from enum import IntEnum, Enum, StrEnum
from string import punctuation
import re
from zoneinfo import ZoneInfo
from coretime import time_hhmm
from stringcase import constcase
from emoji import emojize
import sys
from hashlib import md5
from botyo.threesixfive.data import Data365, LeagueItem, CountryItem, International
from pydantic import BaseModel, Field
from botyo.core.country import Country as Flag
from botyo.unicode_text.emoji import Emoji

WORLD_CUP_ID = 5930


class EventStatus(Enum):
    HT = "HT"
    FT = "FT"
    PPD = "PPD"
    CNL = "CNL"
    AET = "AET"
    NS = "NS"
    JE = "Just Ended"


STATUS_MAP = {
    "Post.": "PPD",
    "Ended": "FT",
    "Canc.": "CNL",
    "Sched.": "NS",
    "Just Ended": "FT",
    "After ET": "AET",
    "After Pen": "AET",
    "Half Time": "HT",
    "2nd Half": "2nd",
    "1st Half": "1st"
}


class GameStatus(StrEnum):
    FT = "Ended"
    JE = "Just Ended"
    SUS = "Susp"
    ABD = "Aband."
    AET = "After Pen"
    NS = "NS"
    FN = "Final"
    PPD = "Post."
    CNL = "Canc."
    HT = "Halftime"
    SECOND_HALF = "2nd Half"
    FIRST_HALF = "1st Half"
    EXTRA_TIME = "Extra Time"
    BEFORE_PENALTIES = "Before Penalties"
    PENALTIES = "Penalties"
    SCHEDULED = "Scheduled"
    NOTVALID = "NA"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return cls.NOTVALID


class ShortGameStatus(StrEnum):
    FIRST_HALF = "1st"
    SECOND_HALF = "2nd"
    FINAL = "Final"
    HALF_TIME = "HT"
    EXTRA_TIME = "ET"
    PENALTIES = "Pen."
    SCHEDULED = "Sched."
    AFTER_PENALTIES = "After Pen"
    BEFORE_PENALTIES = "Before Pen."
    INTO_ET = "Into ET"
    ENDED = "Ended"
    JUSTENDED = "Just Ended"
    SCORE = "Score"
    NOTVALID = "NA"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return cls.NOTVALID


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
    SUBSTITUTION = ":left_arrow:"
    GOAL = ":soccer_ball:"
    YELLOW__CARD = ":yellow_square:"
    RED__CARD = ":red_square:"
    WOODWORK = ":palm_tree:"
    PENALTY__MISS = ":cross_mark:"
    GOAL__DISALLOWED = ":double_exclamation_mark:"


class Event(BaseModel):
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
    startTime: datetime
    intHomeScore: int = Field(default=-1)
    intAwayScore: int = Field(default=-1)
    sort: int = 0
    details: Optional[str] = None
    displayScore: str = Field(default="")
    displayStatus: str = Field(default="")
    source: str = Field(default="")
    strWinDescription: str = Field(default="")

    def __init__(self, **data):
        super().__init__(**data)
        if self.strStatus in STATUS_MAP:
            self.strStatus = STATUS_MAP[self.strStatus]

        delta = (datetime.now(timezone.utc) - self.startTime).total_seconds()
        delta = delta / 60
        try:
            self.displayStatus = GameStatus(self.strStatus).value
            if delta < 0 and self.displayStatus in [GameStatus.NS.value]:
                self.displayStatus = self.startTime.astimezone(
                    ZoneInfo("Europe/London")
                ).strftime("%H:%M")
            else:
                self.displayStatus = self.displayStatus.value
        except Exception:
            self.displayStatus = self.strStatus
        try:
            if re.match(r"^\d+", self.strStatus):
                self.sort = OrderWeight.INPLAY.value * int(self.strStatus)
                self.displayStatus = f'{self.strStatus}"'
            else:
                self.sort = OrderWeight[
                    self.strStatus.translate(punctuation).upper()
                ].value * abs(delta)
        except KeyError:
            self.sort = int(OrderWeight.JUNK.value * abs(delta))
        if any([self.intAwayScore == -1, self.intHomeScore == -1]):
            self.displayScore = ""
        else:
            self.displayScore = ":".join(
                [f"{self.intHomeScore:.0f}", f"{self.intAwayScore:.0f}"]
            )

    @property
    def is_international(self) -> bool:
        try:
            league = next(
                filter(lambda x: x.id == self.idLeague, Data365.leagues), None
            )
            assert league
            return league.is_international
        except AssertionError:
            return False

    @property
    def event_hash(self) -> str:
        return md5(f"{self.event_name}".lower().encode()).hexdigest()

    @property
    def event_name(self) -> str:
        return "/".join([s if s else "" for s in [self.strHomeTeam, self.strAwayTeam]])

    @property
    def inProgress(self) -> bool:
        return re.match(r"^\d+$", self.strStatus) is not None
    
    @property
    def hasEnded(self) -> bool:
        status = EventStatus(self.strStatus)
        return status in [EventStatus.FT, EventStatus.JE, EventStatus.PPD]

    @property
    def win(self) -> str:
        if self.displayStatus == "AET":
            return f"{self.strWinDescription}"
        return ""


class Sport(BaseModel):
    id: int
    name: Optional[str] = None
    nameForURL: Optional[str] = None
    totalGames: int = Field(default=0)
    liveGames: int = Field(default=0)


class Country(BaseModel):
    id: int
    name: str
    nameForURL: Optional[str] = None
    totalGames: int = Field(default=0)
    liveGames: int = Field(default=0)

    @property
    def is_international(self) -> bool:
        return International(self.id) is not International.NOT_INTERNATIONAL


class Competitor(BaseModel):
    id: int
    countryId: int
    sportId: int
    name: str
    nameForURL: str
    mainCompetitionId: int
    type: Optional[int] = None
    color: Optional[str] = None
    popularityRank: Optional[int] = None
    symbolicName: Optional[str] = None
    imageVersion: Optional[int] = None


class StandingRow(BaseModel):
    competitor: Competitor
    gamePlayed: Optional[int] = None
    gamesWon: Optional[int] = None
    gamesLost: Optional[int] = None
    gamesEven: Optional[int] = None
    forward: int = Field(default=0, alias="for")
    against: int = Field(default=0)
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
    unknown: Optional[Any] = None


class StandingGroup(BaseModel):
    num: int
    name: str


class Standing(BaseModel):
    competitionId: int
    groups: Optional[list[StandingGroup]] = None
    seasonNum: Optional[int] = None
    stageNum: Optional[int] = None
    isCurrentStage: Optional[bool] = None
    displayName: Optional[str] = None
    currentGroupCategory: Optional[int] = None
    rows: Optional[list[StandingRow]] = None


class StandingResponse(BaseModel):
    lastUpdateId: int
    requestedUpdateId: int
    ttl: int
    standings: list[Standing]


class Bracket(BaseModel):
    lastUpdateId: int
    requestedUpdateId: int
    ttl: int
    stages: list[Standing]


class BracketsResponse(BaseModel):
    lastUpdateId: int
    requestedUpdateId: int
    ttl: int
    brackets: Bracket


class Competition(BaseModel):
    id: int
    countryId: int
    sportId: int
    name: str
    nameForURL: Optional[str] = None
    popularityRank: Optional[int] = None
    color: Optional[str] = None
    totalGames: Optional[int] = None
    liveGames: Optional[int] = None
    hasActiveGames: Optional[bool] = None
    hasStandings: Optional[bool] = None
    hasBrackets: Optional[bool] = None

    @property
    def flag(self) -> str:
        if International(self.countryId) is International.NOT_INTERNATIONAL:
            return ""
        country = next(
            filter(lambda x: x.id == self.countryId, Data365.countries), None
        )
        assert country
        return Flag(country.name).flag
    
    @property
    def is_international(self) -> bool:
        return International(self.countryId) is not International.NOT_INTERNATIONAL


class GameMember(BaseModel):
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
        try:
            assert self.shortName
            return self.shortName
        except AssertionError:
            return f"{self.name}"


class LineupPosition(BaseModel):
    id: int
    name: str


class MemberStat(BaseModel):
    value: str
    name: str
    shortName: Optional[str] = None


class LineupMember(BaseModel):
    id: int
    status: LineupMemberStatus
    statusText: str
    position: Optional[LineupPosition] = None
    stats: Optional[list[MemberStat]] = None


class Lineup(BaseModel):
    status: Optional[str] = None
    formation: Optional[str] = None
    hasFieldPositions: bool = Field(default=False)
    members: Optional[list[LineupMember]] = None


class GameStatistic(BaseModel):
    id: int
    name: str
    categoryId: int
    categoryName: str
    value: str
    isMajor: Optional[bool]
    valuePercentage: Optional[float]
    isPrimary: Optional[bool]


class GameCompetitor(BaseModel):
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

    @property
    def country(self) -> CountryItem:
        country = next(
            filter(lambda x: x.id == self.countryId, Data365.countries), None
        )
        assert country
        return country

    @property
    def flag(self) -> str:
        try:
            return Flag(self.country.name).flag
        except AssertionError:
            return ""

    @property
    def name_with_flag(self) -> str:
        try:
            return Flag(self.country.name).with_flag(self.name)
        except AssertionError:
            return str(self.name)

    @property
    def score_int(self) -> int:
        try:
            assert self.score is not None
            return self.score
        except AssertionError:
            return -1

    @property
    def shortName(self) -> str:
        try:
            if self.symbolicName:
                return self.symbolicName
            assert self.name
            parts = self.name.split(" ")
            if len(parts) == 1:
                return self.name[:3].upper()
            return f"{parts[0][:1]}{parts[1][:2]}".upper()
        except AssertionError:
            return ""


class OddsRate(BaseModel):
    decimal: Optional[float] = None
    fractional: Optional[str] = None
    american: Optional[str] = None


class OddsOptions(BaseModel):
    num: int
    rate: OddsRate


class Odds(BaseModel):
    lineId: int
    gameId: int
    bookmakerId: int
    lineTypeId: int
    options: list[OddsOptions]


class GameFact(BaseModel):
    id: str
    text: str


class H2HGame(BaseModel):
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime
    statusGroup: int
    statusText: str
    shortStatusText: str
    homeCompetitor: GameCompetitor
    awayCompetitor: GameCompetitor
    winner: int
    scores: list[int]
    roundNum: Optional[int] = None
    seasonNum: Optional[int] = None


class Game(BaseModel):
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime
    statusGroup: int
    statusText: str
    shortStatusText: str
    gameTimeAndStatusDisplayType: int

    homeCompetitor: GameCompetitor
    awayCompetitor: GameCompetitor
    h2hGames: Optional[list[H2HGame]] = None
    odds: Optional[Odds] = None
    roundName: str = Field(default="")
    roundNum: Optional[int] = None
    seasonNum: int = Field(default=0)
    stageNum: int = Field(default=0)
    justEnded: Optional[bool] = None
    hasLineups: Optional[bool] = None
    hasMissingPlayers: Optional[bool] = None
    hasFieldPositions: Optional[bool] = None
    hasTVNetworks: Optional[bool] = None
    hasBetsTeaser: Optional[bool] = None
    matchFacts: Optional[list[GameFact]] = None
    gameTime: Optional[int] = None
    gameTimeDisplay: Optional[str] = None
    winDescription: str = Field(default="")
    aggregateText: str = Field(default="")
    icon: str = Field(default="")

    @property
    def round(self) -> Optional[str]:
        if self.roundNum is None:
            return ""
        return " ".join(
            list(filter(lambda x: x, [f"{self.roundName}", f"{self.roundNum:,0f}"]))
        )

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
            if _status in (GameStatus.FT, GameStatus.AET, GameStatus.JE):
                return True
            return any(
                [
                    _status == GameStatus.HT,
                    _status == GameStatus.PPD,
                    re.match(r"^\d+$", status) is not None,
                ]
            )
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
        match status:
            case GameStatus.HT:
                return "HT"
            case GameStatus.SCHEDULED:
                return self.gameTimeDisplay
            case _:
                return str(status)

    @property
    def displayScore(self) -> str:
        return ":".join(
            [
                f"{max(self.homeCompetitor.score_int, 0):.0f}",
                f"{max(self.awayCompetitor.score_int, 0):.0f}",
            ]
        )

    @property
    def league(self) -> LeagueItem:
        league = next(
            filter(lambda x: x.id == self.competitionId, Data365.leagues), None
        )
        assert league
        return league

    @property
    def displayTitle(self) -> str:
        assert self.homeCompetitor.name
        assert self.awayCompetitor.name
        league = self.league
        assert league
        if league.is_international:
            res = " - ".join(
                [
                    f"{self.homeCompetitor.name_with_flag}",
                    f"{self.awayCompetitor.name_with_flag}",
                ]
            )
        else:
            res = " - ".join(
                [
                    self.homeCompetitor.name,
                    self.awayCompetitor.name,
                ]
            )

        if all([not self.not_started, not self.ended]):
            res = f"{res} {self.displayScore}"
        return res


class EVENT_ICON(Enum):
    SUBSTITUTION = ":left_arrow:"
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


class GameEventType(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    subTypeId: Optional[int] = None
    subTypeName: Optional[str] = None


class GameEvent(BaseModel):
    competitorId: int = Field(default=0)
    eventType: Optional[GameEventType] = None
    statusId: int = Field(default=0)
    stageId: int = Field(default=0)
    order: int = Field(default=0)
    num: int = Field(default=0)
    gameTime: int = Field(default=0)
    addedTime: int = Field(default=0)
    gameTimeDisplay: Optional[str] = None
    gameTimeAndStatusDisplayType: int = Field(default=0)
    playerId: int = Field(default=0)
    isMajor: bool = Field(default=False)
    extraPlayers: Optional[list[int]] = None

    @property
    def order_id(self) -> int:
        return self.order if self.order else 0

    @property
    def is_goal(self) -> bool:
        try:
            assert self.eventType
            assert self.eventType.name
            return self.eventType.name == EVENT_NAME.GOAL.value
        except AssertionError:
            return False

    @property
    def displayTime(self) -> str:
        if not self.gameTimeDisplay:
            return ""
        return self.gameTimeDisplay

    @property
    def playerName(self) -> str:
        return ""


class GameDetails(Game):
    events: Optional[list[GameEvent]] = None
    members: Optional[list[GameMember]] = None

    @property
    def score(self) -> str:
        try:
            assert self.homeCompetitor
            assert self.awayCompetitor
            return ":".join(
                [f"{self.homeCompetitor.score:.0f}", f"{self.awayCompetitor.score:.0f}"]
            )
        except AssertionError:
            return ""


class ResponseGame(BaseModel):
    lastUpdateId: int
    requestedUpdateId: int
    game: GameDetails

    @property
    def events(self) -> list[GameEvent]:
        if not self.game:
            return []
        if not self.game.events:
            return []
        return self.game.events

    @property
    def status(self) -> Optional[str]:
        if not self.game:
            return None
        return self.game.shortStatusText
    
class ResponseH2H(BaseModel):
    game: Game


class ResponseScores(BaseModel):
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


class DetailsEvent(BaseModel):
    time: str
    action: str
    order: int = Field(default=0)
    team: Optional[str] = None
    player: Optional[str] = None
    extraPlayers: Optional[list[str]] = None
    position: Optional[Position] = None
    score: Optional[str] = None

    @property
    def id(self) -> int:
        return self.order if self.order else 0

    @property
    def displayTime(self) -> str:
        return f'{self.time}"'

    @property
    def icon(self) -> str:
        try:
            id = constcase(self.action)
            icon = EVENT_ICON[id]
            return emojize(icon.value)
        except ValueError as e:
            logging.exception(e)
            return ""

    @property
    def icon64(self) -> str:
        try:
            icon = self.icon
            return Emoji.b64(icon)
        except AssertionError:
            return ""


class GoalEvent(BaseModel):
    event_id: int
    game_event_id: int
    time: str
    player: str
    event_name: str
    score: str


class DetailsEventPixel(BaseModel):
    event_id: int
    time: int
    action: str
    is_old_event: bool
    home_team_id: int
    away_team_id: int
    status: Optional[str] = None
    order: int = Field(default=0)
    team: Optional[str] = None
    player: Optional[str] = None
    extraPlayers: Optional[list[str]] = None
    score: Optional[str] = None
    team_id: Optional[int] = None
    event_name: Optional[str] = None
    id: Optional[str] = None
    league_id: Optional[int] = None

    @property
    def order_id(self) -> int:
        return self.order if self.order else 0

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.id = md5(f"{self.event_name}".lower().encode()).hexdigest()

    @property
    def is_goal(self) -> bool:
        try:
            assert self.action
            return self.action.lower() == "goal"
        except AssertionError:
            return False

    @property
    def playerName(self) -> str:
        return self.player if self.player else ""

    @property
    def displayTime(self) -> str:
        if not self.time:
            return ""
        return f"{self.time:.0f}'"

    @classmethod
    def fullTimeEvent(cls, details, league_id):
        assert details.game_time
        assert details.home
        assert details.away
        assert details.event_id
        return cls(
            time=details.game_time,
            action="Full Time",
            is_old_event=False,
            score=details.score,
            event_name=f"{details.home.name}/{details.away.name}",
            event_id=details.event_id,
            order=sys.maxsize,
            status=details.game_status,
            league_id=league_id,
            home_team_id=details.home.id,
            away_team_id=details.away.id,
        )

    @classmethod
    def halfTimeEvent(cls, details, league_id):
        assert details.game_time
        assert details.home
        assert details.away
        assert details.event_id
        return cls(
            time=details.game_time,
            action="Half Time",
            is_old_event=False,
            score=details.score,
            event_name=f"{details.home.name}/{details.away.name}",
            event_id=details.event_id,
            order=sys.maxsize,
            status=details.game_status,
            league_id=league_id,
            home_team_id=details.home.id,
            away_team_id=details.away.id,
        )

    @classmethod
    def startTimeEvent(
        cls, event_name: str, event_id: int, league_id, home_id: int, away_id: int
    ):
        return cls(
            time=0,
            action="Game Start",
            order=0,
            is_old_event=False,
            event_name=event_name,
            event_id=event_id,
            league_id=league_id,
            home_team_id=home_id,
            away_team_id=away_id,
        )


class SubscriptionEvent(BaseModel):
    start_time: datetime
    action: str
    league: str
    league_id: int
    home_team: str
    home_team_id: int
    away_team: str
    away_team_id: int
    event_id: int | str
    event_name: str
    job_id: str
    icon: str
    status: str = Field(default="")
    id: Optional[str] = None
    home_team_icon: Optional[str] = None
    away_team_icon: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        event_name = f"{self.home_team}/{self.away_team}"
        self.id = md5(f"{event_name}".lower().encode()).hexdigest()


class CancelJobEvent(BaseModel):
    job_id: str
    action: str = "Cancel Job"


class SearchResponse(BaseModel):
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


class CompetitionResponse(BaseModel):
    sports: list[Sport]
    countries: list[Country]
    competitions: list[Competition]
    games: list[Game]
    competitors: Optional[list[Competitor]] = None


class OddLineType:
    id: int
    name: str  # "Full Time Result"
    shortName: str  # "1X2"
    title: str  # "Full Time Result"


class OddBoomaker:
    id: int  # 14,
    name: str  # Bet365",
    link: str  # https://www.bet365.com/olp/open-account/?affiliate"
    nameForURL: str  # bet365",
    color: str  # 007B5B",
    imageVersion: int  # 1



class UpdateData(BaseModel):
    message: str | list[DetailsEventPixel] | SubscriptionEvent
    score_message: str
    start_time: datetime
    status: str
    msgId: Optional[str] = None
    icon: Optional[str] = None
    event_id: Optional[int] = None

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
#             "link": "https://www.bet365.com/olp/open-account/?affiliate",
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
#             "link": "https://www.bet365.com/olp/open-account/?affiliate",
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
#             "link": "https://www.bet365.com/olp/open-account/?affiliate=",
#             "trend": 1
#           }
#         ]
#       },
#       "isHomeAwayInverted": false,
#       "hasStandings": true,
#       "standingsName": "Table",
#       "hasBrackets": false,
#       "hasPreviousMeetings": false

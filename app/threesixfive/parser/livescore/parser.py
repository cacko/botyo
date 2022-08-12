from typing import Generator, Optional
from cachable.request import Request
from datetime import datetime, timezone
from cachable.cacheable import CachableFile
from app.threesixfive.item.models import Country, ResponseScores, Sport
from concurrent.futures import ThreadPoolExecutor, as_completed
from botyo_server.scheduler import Scheduler
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from app.core import logger
from app.threesixfive.url import Url
from app.threesixfive.team import (
    normalize_team, DEFAULT_BADGE, store_key, AssetKey
)


@dataclass
class ParserResponse:
    team1: str
    team2: str
    team1Score: int
    team2Score: int
    startTime: datetime
    status: str
    league_id: int
    league: str
    details: str
    team1Id: int
    team2Id: int
    sportId: int
    winDescription: str = ""
    id: Optional[int] =  None


class Badge(CachableFile):

    _name: str
    _url: str
    DEFAULT = DEFAULT_BADGE
    SIZE = (250, 250)

    def __init__(self, name: str, url: str) -> None:
        self._name = normalize_team(name)
        self._url = url
        super().__init__()

    @property
    def filename(self) -> str:
        return f"{store_key(AssetKey.TEAM_BADGE, self._name)}.png"


def badges(badge: Badge):
    with Scheduler.app_context:
        return badge.process()


@dataclass_json
@dataclass
class BadgeQueueItem:
    url: str
    name: str


class BadgeFetcher:

    queue: list[BadgeQueueItem] = None
    isRunning = False
    executor: ThreadPoolExecutor = None
    POOL_SIZE = 10

    def __init__(self):
        self.queue = []

    def add(self, name: str, url: str):
        self.queue.append(BadgeQueueItem(url=url, name=name))
        self.run()

    def _job(self, executor):
        for item in self.queue:
            badge = Badge(**item.to_dict())
            if not badge.isCached:
                yield executor.submit(badges, badge)

    def run(self):
        if self.isRunning:
            return
        self.isRunning = True
        with ThreadPoolExecutor(max_workers=self.POOL_SIZE) as executor:
            for future in as_completed(self._job(executor)):
                try:
                    future.result()
                except Exception as e:
                    logger.error(e, exc_info=True)
            self.isRunning = False


class Parser:

    __endpoint: str
    __struct: ResponseScores = None
    with_details = False
    leagues: list[int] = None

    def __init__(self, with_details=False, leagues: list[int] = []):
        self.__endpoint = Url.livescores(leagues=leagues)
        self.with_details = with_details
        self.leagues = leagues

    def fetch(self):
        req = Request(self.__endpoint)
        json = req.json
        today = datetime.now(tz=timezone.utc).date()
        self.__struct: ResponseScores = ResponseScores.from_dict(json)
        self.__struct.games = [*filter(
            lambda g: g.startTime.date() == today,
            self.__struct.games
        )]

    @property
    def events_total(self) -> int:
        return len(self.__struct.games)

    @property
    def sports(self) -> list[Sport]:
        return self.__struct.sports

    @property
    def countries(self) -> list[Country]:
        return self.__struct.countries

    @property
    def events(self) -> Generator[ParserResponse, None, None]:
        badgeFetcher = BadgeFetcher()
        for game in self.__struct.games:
            yield ParserResponse(
                team1=game.homeCompetitor.name,
                team2=game.awayCompetitor.name,
                team1Score=game.homeCompetitor.score,
                team2Score=game.awayCompetitor.score,
                startTime=game.startTime,
                status=game.shortStatusText
                if game.gameTime < 0 or game.gameTimeDisplay == ""
                else f"{game.gameTime:.0f}",
                league_id=game.competitionId,
                league=game.competitionDisplayName,
                details=Url.game(game.id),
                team1Id=game.homeCompetitor.id,
                team2Id=game.awayCompetitor.id,
                sportId=game.sportId,
                winDescription=game.winDescription,
                id=game.id
            )
            if self.with_details:
                badgeFetcher.add(
                    game.homeCompetitor.name,
                    Url.badge(game.homeCompetitor.id),
                )
                badgeFetcher.add(
                    game.awayCompetitor.name,
                    Url.badge(game.awayCompetitor.id),
                )

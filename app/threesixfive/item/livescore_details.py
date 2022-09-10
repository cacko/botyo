from datetime import datetime, timedelta
from hashlib import blake2b
from .player import Player
from .models import (
    DetailsEvent, DetailsEventPixel, ResponseGame, Position, GameMember, GameCompetitor, GameFact
)
from app.threesixfive.exception import GameNotFound
from cachable.request import Request
from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from unidecode import unidecode
from datetime import timezone
from cachable.cacheable import TimeCacheable
from cachable.models import TimeCache


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ParserDetailsResponse:
    events: Optional[list[DetailsEvent]] = None


class ParseDetailsCache(TimeCache):
    struct: ResponseGame


class ParserDetails(TimeCacheable):

    __url: str
    _struct: ParseDetailsCache = None
    __id: str = None
    cachetime: timedelta = timedelta(seconds=50)

    def __init__(self, url: str, response: ResponseGame = None):
        self.__url = url
        if response is not None:
            self._struct = ParseDetailsCache(
                timestamp=datetime.now(timezone.utc),
                struct=response
            )

    @classmethod
    def get(cls, url: str, response: ResponseGame = None):
        obj = cls(url, response)
        obj.refresh()
        return obj

    def refresh(self):
        if self.load():
            return
        try:
            req = Request(self.__url)
            json = req.json
            res: ResponseGame = ResponseGame.from_dict(json)
            self._struct = self.tocache(res)
            Player.store(res.game)
        except Exception as e:
            logging.exception(e)
            self._struct = None
            raise GameNotFound

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__url.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def events(self) -> list[DetailsEvent]:
        try:
            res = []
            competitors = {
                self._struct.struct.game.homeCompetitor.id:
                self._struct.struct.game.homeCompetitor,
                self._struct.struct.game.awayCompetitor.id:
                self._struct.struct.game.awayCompetitor,
            }
            members = {m.id: m for m in self._struct.struct.game.members}
            if not self._struct.struct.game.events:
                return []
            for ev in self._struct.struct.game.events:
                if ev.competitorId == self._struct.struct.game.homeCompetitor.id:
                    position = Position.HOME
                elif ev.competitorId == self._struct.struct.game.awayCompetitor.id:
                    position = Position.AWAY
                else:
                    position = Position.NONE
                extraPlayers = ev.extraPlayers
                if extraPlayers:
                    extraPlayers = [unidecode(members[pid].displayName)
                                    for pid in extraPlayers]
                res.append(DetailsEvent(
                    time=ev.gameTime,
                    action=ev.eventType.name,
                    position=position,
                    team=competitors[ev.competitorId].name,
                    player=unidecode(members[ev.playerId].displayName),
                    extraPlayers=extraPlayers,
                    order=ev.order))
            return sorted(res, reverse=True, key=lambda x: x.order)
        except Exception:
            return []

    @property
    def events_pixel(self) -> list[DetailsEventPixel]:
        try:
            res = []
            competitors = {
                self._struct.struct.game.homeCompetitor.id:
                self._struct.struct.game.homeCompetitor,
                self._struct.struct.game.awayCompetitor.id:
                self._struct.struct.game.awayCompetitor,
            }
            members = {m.id: m for m in self._struct.struct.game.members}
            if not self._struct.struct.game.events:
                return []
            for ev in self._struct.struct.game.events:
                extraPlayers = ev.extraPlayers
                if extraPlayers:
                    extraPlayers = [unidecode(members[pid].displayName)
                                    for pid in extraPlayers]
                res.append(DetailsEventPixel(
                    event_id=self.event_id,
                    time=ev.gameTime,
                    action=ev.eventType.name,
                    team=competitors[ev.competitorId].name,
                    team_id=ev.competitorId,
                    player=unidecode(members[ev.playerId].displayName),
                    extraPlayers=extraPlayers,
                    score=self.score,
                    is_old_event=self.game_time - ev.gameTime > 5,
                    event_name=f"{self.home.name}/{self.away.name}",
                    order=ev.order))
            return sorted(res, reverse=True, key=lambda x: x.order)
        except Exception:
            return []

    @property
    def event_id(self):
        return self._struct.struct.game.id

    @property
    def score(self) -> str:
        return f"{self.home.score:.0f}:{self.away.score:.0f}"

    @property
    def members(self) -> list[GameMember]:
        return self._struct.struct.game.members

    @property
    def home(self) -> GameCompetitor:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.homeCompetitor

    @property
    def game_time(self) -> int:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.gameTime

    @property
    def facts(self) -> list[GameFact]:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.matchFacts

    @property
    def away(self) -> GameCompetitor:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.awayCompetitor

    @property
    def hasLineups(self) -> bool:
        if any([
            not self.home,
            not self.away
        ]):
            return False
        if any([
            not self.home.lineups,
            not self.away.lineups
        ]):
            return False
        return all([
            self.home.lineups.hasFieldPositions,
            self.away.lineups.hasFieldPositions
        ])

    @property
    def event_name(self) -> str:
        if self.home and self.away:
            return unidecode(
                f"{self.home.name.upper()} vs {self.away.name.upper()}"
            )
        return "Unknown"

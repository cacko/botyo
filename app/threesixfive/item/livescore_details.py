from datetime import datetime, timedelta
from hashlib import blake2b
from .player import Player
from .models import (
    DetailsEvent,
    DetailsEventPixel,
    ResponseGame,
    Position,
    GameMember,
    GameCompetitor,
    GameFact,
)
from app.threesixfive.exception import GameNotFound
from cachable.request import Request
from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from unidecode import unidecode
from datetime import timezone
from cachable.models import TimeCache
from app.core.store import TimeCachable
import logging
from typing import Optional


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ParserDetailsResponse:
    events: Optional[list[DetailsEvent]] = None


class ParseDetailsCache(TimeCache):
    struct: ResponseGame


class ParserDetails(TimeCachable):

    __url: Optional[str] = None
    _struct: Optional[ParseDetailsCache|TimeCache] = None
    __id: Optional[str] = None
    cachetime: timedelta = timedelta(seconds=50)

    def __init__(
        self, url: Optional[str] = None, response: Optional[ResponseGame] = None
    ):
        self.__url = url
        if response is not None:
            self._struct = ParseDetailsCache(
                timestamp=datetime.now(timezone.utc), struct=response
            )

    @classmethod
    def get(cls, url: Optional[str] = None, response: Optional[ResponseGame] = None):
        obj = cls(url, response)
        obj.refresh()
        return obj

    def refresh(self):
        if self.load():
            return
        try:
            req = Request(self.__url)
            json = req.json
            res: ResponseGame = ResponseGame.from_dict(json)  # type: ignore
            self._struct = self.tocache(res)
            Player.store(res.game)
        except Exception as e:
            logging.exception(e)
            self._struct = None
            raise GameNotFound

    @property
    def id(self):
        if not self.__id:
            assert self.__url
            h = blake2b(digest_size=20)
            h.update(self.__url.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def events(self) -> list[DetailsEvent]:
        try:
            res = []
            assert self._struct
            assert self._struct.struct.game.homeCompetitor
            assert self._struct.struct.game.awayCompetitor
            competitors = {
                self._struct.struct.game.homeCompetitor.id: self._struct.struct.game.homeCompetitor,
                self._struct.struct.game.awayCompetitor.id: self._struct.struct.game.awayCompetitor,
            }
            assert self._struct.struct.game.members
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
                players = ev.extraPlayers
                extraPlayers = []
                if players:
                    extraPlayers = [
                        unidecode(members[pid].displayName) for pid in players
                    ]
                assert ev.gameTime
                assert ev.eventType
                assert ev.eventType.name
                res.append(
                    DetailsEvent(
                        time=f"{ev.gameTime:.0f}",
                        action=ev.eventType.name,
                        position=position,
                        team=competitors[ev.competitorId].name,
                        player=unidecode(members[ev.playerId].displayName),
                        extraPlayers=extraPlayers,
                        order=ev.order,
                    )
                )
            return sorted(res, reverse=True, key=lambda x: x.id)
        except Exception as e:
            logging.exception(e)
            return []

    @property
    def events_pixel(self) -> list[DetailsEventPixel]:
        try:
            res = []
            assert self._struct
            assert self._struct.struct.game.homeCompetitor
            assert self._struct.struct.game.awayCompetitor
            competitors = {
                self._struct.struct.game.homeCompetitor.id: self._struct.struct.game.homeCompetitor,
                self._struct.struct.game.awayCompetitor.id: self._struct.struct.game.awayCompetitor,
            }
            assert self._struct.struct.game.members
            members = {m.id: m for m in self._struct.struct.game.members}
            if not self._struct.struct.game.events:
                return []
            for ev in self._struct.struct.game.events:
                players = ev.extraPlayers
                extraPlayers = []
                if players:
                    extraPlayers = [
                        unidecode(members[pid].displayName) for pid in players
                    ]
                assert self.event_id
                assert ev.gameTime
                assert ev.eventType
                assert ev.eventType.name
                assert self.game_time
                assert self.home
                assert self.away
                res.append(
                    DetailsEventPixel(
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
                        order=ev.order,
                        status=self.game_status,
                    )
                )
            return sorted(res, reverse=True, key=lambda x: x.order_id)
        except Exception as e:
            logging.exception(e)
            return []

    @property
    def event_id(self):
        if self._struct:
            return self._struct.struct.game.id
        
    @property
    def game_status(self) -> str:
        if self._struct:
            return self._struct.struct.game.shortStatusText
        return ""
    
    @property
    def score(self) -> str:
        try:
            assert self.home
            assert self.away
            return f"{self.home.score:.0f}:{self.away.score:.0f}"
        except AssertionError:
            return ""

    @property
    def members(self) -> Optional[list[GameMember]]:
        if self._struct:
            return self._struct.struct.game.members

    @property
    def home(self) -> Optional[GameCompetitor]:
        if not self._struct or not self._struct.struct.game:
            return None
        return self._struct.struct.game.homeCompetitor

    @property
    def game_time(self) -> Optional[int]:
        if not self._struct or not self._struct.struct.game:
            return None
        return self._struct.struct.game.gameTime

    @property
    def facts(self) -> Optional[list[GameFact]]:
        if not self._struct or not self._struct.struct.game:
            return None
        return self._struct.struct.game.matchFacts

    @property
    def away(self) -> Optional[GameCompetitor]:
        if not self._struct or not self._struct.struct.game:
            return None
        return self._struct.struct.game.awayCompetitor

    @property
    def hasLineups(self) -> bool:
        try:
            assert self.home
            assert self.home.lineups
            assert self.away
            assert self.away.lineups
            return all(
                [self.home.lineups.hasFieldPositions, self.away.lineups.hasFieldPositions]
            )
        except AssertionError:
            return False

    @property
    def event_name(self) -> str:
        try:
            assert self.home
            assert self.away
            assert self.home.name
            assert self.away.name
            return unidecode(f"{self.home.name.upper()} vs {self.away.name.upper()}")
        except AssertionError:
            return "Unknown"

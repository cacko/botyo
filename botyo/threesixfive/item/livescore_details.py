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
)
from botyo.threesixfive.exception import GameNotFound
from cachable.request import Request
from typing import Optional
from unidecode import unidecode
from datetime import timezone
from cachable.models import TimeCache
from botyo.core.store import TimeCachable
import logging
from pydantic import BaseModel


class ParserDetailsResponse(BaseModel):
    events: Optional[list[DetailsEvent]] = None


class ParseDetailsCache(TimeCache):
    struct: ResponseGame


class ParserDetails(TimeCachable):

    __url: Optional[str] = None
    _struct: Optional[ParseDetailsCache | TimeCache] = None
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
            res = ResponseGame(**json)  # type: ignore
            self._struct = self.tocache(res)
            Player.store(res.game)
        except AssertionError:
            pass
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
                homeCompetitor = self._struct.struct.game.homeCompetitor
                awayCompetitor = self._struct.struct.game.awayCompetitor
                if ev.competitorId == homeCompetitor.id:
                    position = Position.HOME
                elif ev.competitorId == awayCompetitor.id:
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
                extraPlayers = [unidecode(members[pid].displayName) for pid in players]
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
                    home_team_id=self.home.id,
                    away_team_id=self.away.id,
                )
            )
        return sorted(res, reverse=True, key=lambda x: x.order_id)

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
    def display_status(self) -> str:
        if self._struct:
            return self._struct.struct.game.displayStatus
        return ""

    @property
    def score(self) -> str:
        try:
            assert self.home
            assert self.away
            return f"{self.home.score_int:.0f}:{self.away.score_int:.0f}"
        except AssertionError as e:
            logging.error(e)
            return ""

    @property
    def members(self) -> Optional[list[GameMember]]:
        if self._struct:
            return self._struct.struct.game.members
        return None

    @property
    def home(self) -> Optional[GameCompetitor]:
        if not all([self._struct, self._struct.struct.game]):
            return None
        return self._struct.struct.game.homeCompetitor

    @property
    def game_time(self) -> Optional[int]:
        try:
            assert self._struct
            assert self._struct.struct.game
            assert self._struct.struct.game.gameTime > 0
            return self._struct.struct.game.gameTime
        except AssertionError as e:
            logging.error(e)
            return None

    @property
    def away(self) -> Optional[GameCompetitor]:
        if not all([self._struct, self._struct.struct.game]):
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
                [
                    self.home.lineups.hasFieldPositions,
                    self.away.lineups.hasFieldPositions,
                ]
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
        except AssertionError as e:
            logging.exception(e)
            return "Unknown"

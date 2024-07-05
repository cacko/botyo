from .models import (
    Competitor,
    Game,
    SearchResponse,
)
from cachable.request import Request
from cachable.models import TimeCache
from hashlib import blake2s
from botyo.threesixfive.url import Url
from datetime import datetime, timedelta, timezone
from typing import Optional
from botyo.core.store import RedisCachable, TimeCachable
from pydantic import BaseModel


class TeamStruct(BaseModel):
    competitors: list[Competitor]
    games: list[Game]


class TeamCache(TimeCache):
    struct: TeamStruct


class TeamSearch(RedisCachable):
    __struct: Optional[Competitor] = None
    __query: str = ""

    def __init__(self, query: str):
        self.__query = query.lower()

    def __fetch(self):
        req = Request(Url.search(self.__query))
        json = req.json
        results: list[Competitor] = SearchResponse(**json).results
        self.__struct = results[0] if len(results) else None
        return self.tocache(self.__struct)

    def load(self) -> bool:
        if self.__struct is not None:
            return True
        if not self.isCached:
            return False
        self.__struct = self.fromcache()
        return True if self.__struct else False

    @property
    def id(self):
        h = blake2s(digest_size=20)
        h.update(self.__query.encode())
        return h.hexdigest()

    @property
    def competitor(self) -> Optional[Competitor]:
        if not self.load():
            self.__fetch()
        return self.__struct


class Team(TimeCachable):
    _struct: Optional[TeamCache] = None
    __competitor_id: int = 0
    cachetime: timedelta = timedelta(seconds=20)

    def __init__(self, competitor_id: int):
        self.__competitor_id = competitor_id

    def isExpired(self, t: datetime) -> bool:
        return datetime.now(tz=timezone.utc) - t > self.cachetime

    def load(self) -> bool:
        try:
            assert self._struct
            assert self.isCached
            self._struct = self.fromcache()
            assert self._struct
        except AssertionError:
            return False
        return True

    def __fetch(self):
        req = Request(Url.team_games(self.__competitor_id))
        json = req.json
        team = TeamStruct(**json)
        return self.tocache(team)

    @property
    def id(self):
        return self.__competitor_id

    @property
    def team(self) -> TeamStruct:
        try:
            assert self.load()
        except AssertionError:
            self._struct = self.__fetch()
        try:
            assert self._struct
            return self._struct.struct
        except AssertionError:
            return None

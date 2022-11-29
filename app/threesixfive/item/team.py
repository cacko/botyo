from .models import (
    Competitor,
    Game,
    SearchResponse,
)
from cachable.request import Request
from cachable.models import TimeCache
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from hashlib import blake2s
from app.threesixfive.url import Url
from datetime import timedelta
from typing import Optional
from app.core.store import RedisCachable, TimeCachable


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TeamStruct:
    competitors: list[Competitor]
    games: list[Game]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
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
        results: list[Competitor] = SearchResponse.from_dict(json).results  # type: ignore
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

    # def isExpired(self, *args, **kwargs) -> bool:
    #     return True

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()  # type: ignore
        return True if self._struct else False

    def __fetch(self):
        req = Request(Url.team_games(self.__competitor_id))
        json = req.json
        team: TeamStruct = TeamStruct.from_dict(json)  # type: ignore
        return self.tocache(team)

    @property
    def id(self):
        return self.__competitor_id

    @property
    def team(self) -> TeamStruct:
        if not self.load():
            self._struct = self.__fetch()  # type: ignore
        return self._struct.struct if self._struct else None  # type: ignore

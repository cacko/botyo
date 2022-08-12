from .models import (
    Competition,
    CompetitionResponse,
    Country,
    Game,
)
from cachable.request import Request
from cachable.cacheable import TimeCacheable
from cachable.models import TimeCache
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from hashlib import blake2s
from app.threesixfive.url import Url
from datetime import timedelta


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CompetitionCache(TimeCache):
    struct: CompetitionResponse


class CompetitionData(TimeCacheable):
    _struct: CompetitionCache = None
    __competition_id: int = 0
    cachetime: timedelta = timedelta(minutes=5)

    def __init__(self, competition_id: int):
        self.__competition_id = competition_id


    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    def __fetch(self):
        req = Request(Url.competition_schedule(self.__competition_id))
        json = req.json
        response: CompetitionResponse = CompetitionResponse.from_dict(json)
        return  self.tocache(response)

    @property
    def id(self):
        return self.__competition_id


    @property
    def competition(self) -> Competition:
        if not self.load():
            self._struct = self.__fetch()
            if not self._struct:
                return None
        return self._struct

    @property
    def games(self) -> list[Game]:
        if not self.load():
            self._struct = self.__fetch()
            if not self._struct:
                return None
        return self._struct.struct.games

    @property
    def country(self) -> Country:
        if not self.load():
            self._struct = self.__fetch()
            if not self._struct:
                return None
        return self._struct.struct.countries[0
         ]

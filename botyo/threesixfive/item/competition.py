from .models import (
    Competition,
    CompetitionResponse,
    Country,
    Game,
)
from cachable.request import Request
from cachable.models import TimeCache
from botyo.threesixfive.url import Url
from datetime import timedelta
from botyo.core.store import TimeCachable
from typing import Optional
import logging


class CompetitionCache(TimeCache):
    struct: CompetitionResponse


class CompetitionData(TimeCachable):
    _struct: Optional[CompetitionCache] = None
    __competition_id: int = 0
    cachetime: timedelta = timedelta(minutes=5)

    def __init__(self, competition_id: int):
        self.__competition_id = competition_id

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()  # type:ignore
        return True if self._struct else False

    def __fetch(self):
        req = Request(Url.competition_schedule(self.__competition_id))
        json = req.json
        response = CompetitionResponse(**json)
        logging.debug(response)
        return self.tocache(response)

    @property
    def id(self):
        return self.__competition_id

    @property
    def competition(self) -> Optional[Competition]:
        if not self.load():
            self._struct = self.__fetch()  # type: ignore
            if not self._struct:
                return None
        return self._struct.struct.competitions[0]  # type: ignore

    @property
    def games(self) -> Optional[list[Game]]:
        if not self.load():
            self._struct = self.__fetch()  # type: ignore
            if not self._struct:
                return None
        return self._struct.struct.games  # type: ignore

    @property
    def country(self) -> Optional[Country]:
        if not self.load():
            self._struct = self.__fetch()  # type: ignore
            if not self._struct:
                return None
        return self._struct.struct.countries[0]  # type: ignore

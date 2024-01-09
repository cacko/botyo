from botyo.threesixfive.url import Url
from .models import Event, H2HGame
from botyo.core.store import RedisCachable
from typing import Optional
import logging
from cachable.request import Request


class H2H(RedisCachable):

    __item: Event

    def __init__(self, item: Event):
        self.__item = item

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    @property
    def id(self):
        return f"{self.__item.id}"
    
    @property
    def isCached(self) -> bool:
        return False

    @property
    def games(self) -> Optional[list[H2HGame]]:
        try:
            if not self.load():
                self.__fetch()
            assert self._struct
            return self._struct
        except AssertionError:
            return None

    def __fetch(self):
        try:
            req = Request(Url.h2h(self.__item.idEvent))
            logging.warn(Url.h2h(self.__item.idEvent))
            json = req.json
            logging.warn(json)
            details = ResponseGame(**json)  # type: ignore
            assert details
            assert details.h2hGames
            self._struct = details.h2hGames
            return self.tocache(self._struct)
        except AssertionError as e:
            logging.exception(e)
            return None

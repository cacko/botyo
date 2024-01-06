from .livescore_details import ParserDetails
from .models import Event, H2HGame
from botyo.core.store import RedisCachable
from typing import Optional
import logging


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
            details = ParserDetails.get(self.__item.details)
            assert details
            assert details.h2hGames
            self._struct = detals.hh2hGames
            return self.tocache(self._struct)
        except AssertionError as e:
            logging.exception(e)
            return None

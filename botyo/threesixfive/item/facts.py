from .livescore_details import ParserDetails
from .models import GameFact, Event
from botyo.core.store import RedisCachable
from typing import Optional


class Facts(RedisCachable):

    __item: Optional[Event] = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def id(self):
        assert self.__item
        return f"facts:{self.__item.id}"

    @property
    def facts(self) -> Optional[list[GameFact]]:
        try:
            if not self.load():
                assert self.__item
                details = ParserDetails.get(self.__item.details)
                res = self.tocache(details.facts)
                assert res
                self._struct: list[GameFact] = res
            return self._struct
        except AssertionError:
            return None

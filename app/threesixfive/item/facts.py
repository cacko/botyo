from .livescore_details import ParserDetails
from .models import GameFact, Event
from cachable.cacheable import Cachable


class Facts(Cachable):

    __item: Event = None
    _struct: list[GameFact] = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def id(self):
        return f"facts:{self.__item.id}"

    @property
    def facts(self) -> list[GameFact]:
        if not self.load():
            details = ParserDetails.get(self.__item.details)
            self._struct: list[GameFact] = self.tocache(details.facts)
        if not self._struct:
            return None
        return self._struct


from cachable.request import Request
from botyo.core.store import RedisCachable
from botyo.threesixfive.data import LeagueItem
from botyo.threesixfive.item.models import Standing, StandingResponse
from botyo.threesixfive.url import Url


class Standings(RedisCachable):

    __league: LeagueItem
    _struct: StandingResponse

    def __init__(self, league: LeagueItem):
        self.__league = league

    @property
    def id(self):
        return f"{self.__league.league_id}"

    def standing(self, refresh=True) -> Standing:
        if not self.load() or refresh:
            self._struct = self.__fetch()
        return self._struct.standings[0]

    def __fetch(self):
        req = Request(Url.standings(self.__league.league_id))
        json = req.json
        self._struct = StandingResponse(**json)  # type: ignore
        return self.tocache(self._struct)

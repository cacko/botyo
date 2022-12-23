from dataclasses import dataclass
from dataclasses_json import dataclass_json
from botyo.threesixfive.item.models import GameCompetitor
from .livescore_details import ParserDetails
from .models import Event, GameMember, LineupMember, LineupMemberStatus
from botyo.core.store import RedisCachable
from typing import Optional


@dataclass_json
@dataclass
class TeamLineup:
    lineup: list[LineupMember]
    team: GameCompetitor


@dataclass_json
@dataclass
class LineupCache:
    home: TeamLineup
    away: TeamLineup
    members: list[GameMember]


class Lineups(RedisCachable):

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
    def lineups(self) -> Optional[LineupCache]:
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
            home = details.home
            away = details.away
            if any([
                not details.members,
                not details.hasLineups,
            ]):
                return None
            assert home
            assert home.lineups
            assert home.lineups.members
            assert away
            assert away.lineups
            assert away.lineups.members
            assert details
            assert details.members
            self._struct = LineupCache(
                home=TeamLineup(team=home, lineup=self.__getStarting(
                    home.lineups.members)),
                away=TeamLineup(team=away, lineup=self.__getStarting(
                    away.lineups.members)),
                members=details.members
            )
            return self.tocache(self._struct)
        except AssertionError:
            return None

    def __getStarting(self, members: list[LineupMember]) -> list[LineupMember]:
        return list(filter(
            lambda x: x.status == LineupMemberStatus.STARTING,
            members))

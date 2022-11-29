from dataclasses import dataclass
from dataclasses_json import dataclass_json
from app.threesixfive.item.models import GameCompetitor
from .livescore_details import ParserDetails
from .models import Event, GameMember, LineupMember, LineupMemberStatus
from app.core.store import RedisCachable

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
    _struct: LineupCache = None

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
    def lineups(self) -> LineupCache:
        if not self.load():
            self.__fetch()
        return self._struct

    def __fetch(self):
        details = ParserDetails.get(self.__item.details)
        home = details.home
        away = details.away
        if any([
            not details.members,
            not details.hasLineups,
        ]):
            return None
        self._struct = LineupCache(
            home=TeamLineup(team=home, lineup=self.__getStarting(
                home.lineups.members)),
            away=TeamLineup(team=away, lineup=self.__getStarting(
                away.lineups.members)),
            members=details.members
        )
        return self.tocache(self._struct)

    def __getStarting(self, members: list[LineupMember]) -> list[LineupMember]:
        return list(filter(
            lambda x: x.status == LineupMemberStatus.STARTING,
            members))

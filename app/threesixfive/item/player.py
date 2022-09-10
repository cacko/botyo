from typing import Optional
from app.threesixfive.data import Data365
from app.threesixfive.exception import PlayerNotFound
from .models import (
    GameCompetitor,
    GameMember,
    GameDetails,
    LineupMember,
)
from cachable.cacheable import CachableFile, Cachable
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, config
from fuzzelinho import Match, MatchMethod
from enum import Enum
import pickle
from unidecode import unidecode
from datetime import datetime
from marshmallow import fields
from hashlib import blake2b

from cachable.storage import Storage


class InternationalCompetitions(Enum):
    AFRICA = "Africa"
    EUROPE = "Europe"
    INTERNATIONAL = "International"


class PlayerMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class PlayerNeedle:
    name: str


class PlayerImage(CachableFile):

    member: GameMember = None
    team: str = None
    URL_TEMPLATE = "https://imagecache.365scores.com/image/upload/" \
        "f_png,w_200," \
        "h_200,c_limit,q_auto:eco,dpr_2,d_Athletes:{member.athleteId}.png," \
        "r_max,c_thumb,g_face,z_0.65/v{member.imageVersion}/Athletes" \
        "/{team}/{member.athleteId}"
    __id: str = None

    def __init__(self, member, team: str = None):
        self.member = member
        self.team = team

    @property
    def url(self):
        return self.URL_TEMPLATE.format(member=self.member, team=self.team)

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(f"{self.member.name}-{self.team}".encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def filename(self) -> str:
        return f"{self.id}.png"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlayerGame:
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    shortStatusText: str
    gameTimeAndStatusDisplayType: int
    gameTime: int
    gameTimeDisplay: str
    teamId: Optional[int] = None
    teamName: Optional[str] = None


@dataclass_json
@dataclass
class PlayerStruct:
    game: PlayerGame
    member: GameMember
    lineupMember: LineupMember


class Player(Cachable):

    _struct: PlayerStruct = None

    def __init__(
        self, game: PlayerGame, member: GameMember, lineupMember: LineupMember
    ):
        self._struct = PlayerStruct(
            game=game, member=member, lineupMember=lineupMember)

    @classmethod
    def store(cls, game: GameDetails):
        try:
            members = game.members
            competitors = {
                game.homeCompetitor.id: game.homeCompetitor,
                game.awayCompetitor.id: game.awayCompetitor,
            }
            for lineupMember in [
                *game.homeCompetitor.lineups.members,
                *game.awayCompetitor.lineups.members,
            ]:
                member: GameMember = next(
                    filter(lambda x: x.id == lineupMember.id, members), None)
                game: PlayerGame = PlayerGame.from_dict(game.to_dict())
                team: GameCompetitor = competitors[member.competitorId]
                game.teamId = team.id
                game.teamName = team.name
                obj = cls(game, member, lineupMember)
                obj.tocache(obj._struct)
        except AttributeError:
            pass

    @classmethod
    def find(cls, query):
        haystack = [PlayerNeedle(name=k.decode())
                    for k in Storage.hkeys(cls.hash_key)]
        matches = PlayerMatch(haystack=haystack).fuzzy(
            PlayerNeedle(name=query))
        if not matches:
            raise PlayerNotFound
        data = Storage.hget(cls.hash_key, matches[0].name.encode())
        if not data:
            return PlayerNotFound
        struct = PlayerStruct.from_dict(pickle.loads(data))
        return cls(
            game=struct.game,
            member=struct.member,
            lineupMember=struct.lineupMember
        )

    def fromcache(self):
        if data := Storage.hget(__class__.hash_key, self.id):
            return PlayerStruct.from_dict(pickle.loads(data))
        return None

    def tocache(self, res):
        Storage.pipeline().hset(
            __class__.hash_key, self.id, pickle.dumps(res.to_dict())
        ).persist(__class__.hash_key).execute()
        return res

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    @property
    def isCached(self) -> bool:
        return Storage.hexists(self.store_key, self.id) == 1

    @property
    def id(self):
        return unidecode(self._struct.member.name)

    @property
    def image(self) -> PlayerImage:
        isNational = self.isNationalTeam
        team = "NationalTeam" if isNational else None
        return PlayerImage(self._struct.member, team=team)

    @property
    def isNationalTeam(self) -> bool:
        game: PlayerGame = self._struct.game
        leagues = Data365.leagues
        competition = next(
            filter(lambda x: x.id == game.competitionId, leagues), None)
        country_name = competition.country_name if competition else ""
        logging.debug(f">> Country {country_name}")
        if not country_name:
            return False
        try:
            if self._struct.game.teamName != country_name:
                return False
            _ = InternationalCompetitions(country_name)
            return True
        except Exception:
            return False

    @property
    def member(self) -> GameMember:
        return self._struct.member

    @property
    def lineupMember(self) -> LineupMember:
        return self._struct.lineupMember

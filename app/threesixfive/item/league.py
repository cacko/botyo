

from hashlib import blake2b

from cachable.cacheable import Cachable, CachableFile, TimeCacheable

from app.core.image import pixelme_b64
from app.threesixfive.url import Url


class LeagueImage(CachableFile):

    __id: str = None
    _league_id = None

    def __init__(self, league_id: int):
        self._league_id = league_id

    @property
    def url(self):
        return Url.competition_logo(self._league_id)

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(f"{self.url}".encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def filename(self) -> str:
        return f"{self.id}.png"


class LeagueImagePixel(Cachable):

    __league_id: str
    __id = None

    def __init__(self, league_id) -> None:
        self.__league_id = league_id

    @property
    def base64(self) -> str:
        if not self.load():
            team = LeagueImage(self.__league_id)
            path = team.path
            self._struct = pixelme_b64(path, resize=(8, 8))
            self.tocache(self._struct)
        return self._struct

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(f"{self.__league_id}".encode())
            self.__id = h.hexdigest()
        return self.__id

# class LeagueSchedule(TimeCacheable):
#     _struct: TeamCache = None
#     __competitor_id: int = 0
#     cachetime: timedelta = timedelta(hours=1)

#     def __init__(self, competitor_id: int):
#         self.__competitor_id = competitor_id

#     # def isExpired(self, *args, **kwargs) -> bool:
#     #     return True

#     def load(self) -> bool:
#         if self._struct is not None:
#             return True
#         if not self.isCached:
#             return False
#         self._struct = self.fromcache()
#         return True if self._struct else False

#     def __fetch(self):
#         req = Request(Url.team_games(self.__competitor_id))
#         json = req.json
#         team: TeamStruct = TeamStruct.from_dict(json)
#         return self.tocache(team)

#     @property
#     def id(self):
#         return self.__competitor_id

#     @property
#     def team(self) -> TeamStruct:
#         if not self.load():
#             self._struct = self.__fetch()
#         return self._struct.struct if self._struct else None

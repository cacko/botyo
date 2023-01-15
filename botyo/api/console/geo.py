from argparse import ArgumentTypeError
from functools import reduce
from typing import Optional
from cachable.request import Request
from dataclasses_json import dataclass_json, Undefined
from dataclasses import dataclass
from botyo.core.config import Config
from validators import ip_address, domain
import socket
from botyo.server.output import TextOutput, Column
from botyo.core.country import Country


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GeoISP:
    id: int
    name: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GeoLookup:
    ISP: Optional[GeoISP] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_iso: Optional[str] = None
    ip: Optional[str] = None
    location: Optional[list[float]] = None
    subdivisions: Optional[str] = None
    timezone: Optional[str] = None

    @property
    def gps(self):
        if not self.location:
            return None
        loc = self.location
        return f"https://maps.google.com/?q={loc[0]:.3f},{loc[1]:.3f}"

    @property
    def isp(self):
        if not self.ISP:
            return None
        return f"{self.ISP.name} ({self.ISP.id})"

    @property
    def country_with_flag(self):
        if self.country:
            return Country(name=self.country).with_flag()


class GeoMeta(type):
    _instances: dict[str, "Geo"] = {}
    _app = None
    _api = None

    def __call__(cls, query: str, *args, **kwds):
        if query not in cls._instances:
            cls._instances[query] = type.__call__(cls, query, *args, **kwds)
        return cls._instances[query]

    @property
    def api_url(cls):
        return Config.geo.base_url

    def find(cls, query):
        return cls(query).lookup()


class Geo(object, metaclass=GeoMeta):

    __ip: str
    __lookup_result: Optional[GeoLookup] = None

    def __init__(self, query) -> None:
        if ip_address.ipv4(query):
            self.__ip = query
        elif domain(query):
            self.__ip = socket.gethostbyname(query)
        if not self.__ip:
            raise ArgumentTypeError

    @property
    def lookup_result(self):
        if not self.__lookup_result:
            req = Request(f"{__class__.api_url}/api/lookup", params={"ip": self.__ip})
            json = req.json
            self.__lookup_result = GeoLookup.from_dict(json)  # type: ignore

        return self.__lookup_result

    def lookup(self) -> str:
        result = self.lookup_result
        if not result:
            return ""
        data = filter(
            lambda x: x[0],
            [
                (result.country_with_flag, "Country"),
                (result.city, "City"),
                (result.subdivisions, "Area"),
                (result.timezone, "Timezone"),
                (result.gps, "Location"),
                (result.isp, "ISP"),
            ],
        )
        cols, row = reduce(
            lambda r, cr: (
                [*r[0], Column(title=cr[1], fullsize=True, size=40)],
                [*r[1], cr[0]],
            ),
            data,
            ([], []),
        )
        TextOutput.addRobustTable(cols, [row])
        return TextOutput.render()

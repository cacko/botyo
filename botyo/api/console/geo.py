from argparse import ArgumentTypeError
from functools import reduce
from typing import Optional
from cachable.request import Request
from botyo.core.config import Config
from validators import ip_address, domain
import socket
from botyo.server.output import TextOutput, Column
from botyo.core.country import Country
from pydantic import BaseModel, Extra
import re
from argparse import ArgumentParser
from corestring import split_with_quotes
from botyo.core import normalize_prompt

RE_GPS = re.compile(r"^(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)")


class GeoISP(BaseModel, extra=Extra.ignore):
    id: int
    name: str


class GeoLookup(BaseModel, extra=Extra.ignore):
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


class GeoLocation(BaseModel):
    country: str
    country_iso: str
    city: str
    name: str
    subdivions: Optional[list[str]] = None
    addressLine: Optional[str] = None
    postCode: Optional[str] = None
    location: Optional[list[float]] = None

    @property
    def gps(self):
        if not self.location:
            return None
        loc = self.location
        return f"https://maps.google.com/?q={loc[0]:.3f},{loc[1]:.3f}"

    @property
    def country_with_flag(self):
        if self.country:
            return Country(name=self.country).with_flag()


class GeoMeta(type):
    _instances: dict[str, "GeoIP"] = {}
    _app = None
    _api = None

    def __call__(cls, query: str, *args, **kwds):
        if query not in cls._instances:
            cls._instances[query] = type.__call__(cls, query, *args, **kwds)
        return cls._instances[query]

    @property
    def api_url(cls):
        return Config.geo.base_url


class GeoBase(object):

    def output(self, lines: list[tuple[str, str]]):
        data = filter(
            lambda x: x[0],
            lines,
        )
        cols, row = reduce(  # type: ignore
            lambda r, cr: (  # type: ignore
                [*r[0], Column(title=cr[1], fullsize=True, size=40)],
                [*r[1], cr[0]],
            ),
            data,
            ([], []),
        )
        TextOutput.addRobustTable(cols, [row])
        return TextOutput.render()


class GeoIP(GeoBase, metaclass=GeoMeta):

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
            req = Request(f"{__class__.api_url}/api/ip/{self.__ip}")
            json = req.json
            self.__lookup_result = GeoLookup(**json)  # type: ignore

        return self.__lookup_result

    def lookup(self) -> str:
        result = self.lookup_result
        if not result:
            return ""
        return self.output([
            (result.country_with_flag, "Country"),
            (result.city, "City"),
            (result.subdivisions, "Area"),
            (result.timezone, "Timezone"),
            (result.gps, "Location"),
            (result.isp, "ISP"),
        ])


class GeoCoderParams(BaseModel):
    query: list[str]
    coder: Optional[str] = None


class GeoCoder(GeoBase, metaclass=GeoMeta):

    __path: str
    __lookup_result: Optional[GeoLocation] = None
    __params: GeoCoderParams

    def __init__(self, query) -> None:
        self.__params = self.coder_params(query)
        query = " ".join(self.__params.query)
        self.__path = f"address/{query.strip()}"
        if m := RE_GPS.match(query.strip()):
            self.__path = f"gps/{m.group(1)}/{m.group(3)}"

    @property
    def arg_parser(self) -> ArgumentParser:
        parser = ArgumentParser(description="QR Processing",
                                exit_on_error=False)
        parser.add_argument("query", nargs="+")
        parser.add_argument("-c",
                            "--coder",
                            type=str)
        return parser

    def coder_params(
        self,
        prompt: Optional[str]
    ) -> GeoCoderParams:
        parser = self.arg_parser
        if not prompt:
            return GeoCoderParams(query=[""])
        namespace, _ = parser.parse_known_args(
            split_with_quotes(normalize_prompt(prompt))
        )
        return GeoCoderParams(**namespace.__dict__)

    @property
    def lookup_result(self):
        if not self.__lookup_result:
            params_dict = self.__params.dict()
            del params_dict["query"]
            params = {k: v for k, v in params_dict.items() if v}
            req = Request(f"{__class__.api_url}/api/{self.__path}", params=params)
            json = req.json
            self.__lookup_result = GeoLocation(**json)  # type: ignore

        return self.__lookup_result

    def lookup(self) -> str:
        result = self.lookup_result
        if not result:
            return ""
        return self.output([
            (result.country_with_flag, "Country"),
            (result.city, "City"),
            (", ".join(result.subdivions), "Area"),
            (result.postCode, "Post Code"),
            (result.gps, "Location"),
            (result.addressLine, "Address"),
        ])

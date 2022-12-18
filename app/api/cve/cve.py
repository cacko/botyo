from app.api.cve.components import CVEHeader
from cachable.request import Request
from datetime import timedelta
from cachable.cacheable import TimeCacheable
from cachable.storage import StorageMeta
from cachable.storage.redis import RedisStorage
from stringcase import alphanumcase
from botyo_server.output import TextOutput
from .models import CVEResponse
from typing import Optional


class CVECachable(TimeCacheable):
    @property
    def storage(self) -> StorageMeta:
        return RedisStorage


class CVE(CVECachable):
    cachetime: timedelta = timedelta(minutes=30)

    __query: Optional[str] = None
    __ignoreCache: bool = False

    def __init__(self, query: Optional[str] = None, ignoreCache: bool = False) -> None:
        self.__query = query
        self.__ignoreCache = ignoreCache
        super().__init__()

    @property
    def id(self):
        if self.__query:
            return f"query{alphanumcase(self.__query)}"
        return "recent"

    def fetch(self):
        args = {}
        if self.__query:
            args["keyword"] = self.__query
        req = Request("https://services.nvd.nist.gov/rest/json/cves/1.0", params=args)
        return self.tocache(CVEResponse.from_dict(json))  # type: ignore

    @property
    def response(self) -> Optional[CVEResponse]:
        try:
            isLoaded = self.load()
            if self.__ignoreCache or (not isLoaded):
                self._struct = self.fetch()
            assert self._struct
            return self._struct.struct
        except AssertionError:
            return None

    @property
    def message(self) -> str:
        assert self.response
        response: CVEResponse = self.response
        rows = [
            CVEHeader(cve.id, cve.description, cve.severity, cve.attackVector)
            for cve in response.result.CVE_Items
        ]
        TextOutput.addRows(rows)
        return TextOutput.render()

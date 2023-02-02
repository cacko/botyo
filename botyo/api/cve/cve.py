from botyo.api.cve.components import CVEHeader
from cachable.request import Request
from datetime import timedelta
from cachable.cacheable import TimeCacheable
from cachable.storage.meta import StorageMeta
from cachable.storage.redis import RedisStorage
from stringcase import alphanumcase
from botyo.server.output import TextOutput
from .models import CVEResponse
from typing import Optional
import re
import logging

CVE_ID_MATCH = re.compile(r'^(CVE-\d+-\d+)\s(.+)', re.IGNORECASE)


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
        query = self.__query.strip()
        if cve_match := CVE_ID_MATCH.search(self.__query):
            args["cveId"] = cve_match.group(1)
            args["keywordSearch"] = cve_match.group(2)
        elif query:
            args["keywordSearch"] = query
        req = Request("https://services.nvd.nist.gov/rest/json/cves/2.0", params=args)
        json = req.json
        logging.debug(json)
        return self.tocache(CVEResponse(**json))

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
            CVEHeader(cve.cve.id, cve.cve.description, cve.cve.severity, cve.cve.attackVector)
            for cve in response.vulnerabilities
        ]
        TextOutput.addRows(rows)
        return TextOutput.render()

from app.api.cve.components import CVEHeader
from cachable.request import Request
from datetime import timedelta
from cachable.cacheable import TimeCacheable
from stringcase import alphanumcase
from botyo_server.output import TextOutput
from .models import CVEResponse


class CVE(TimeCacheable):
    cachetime: timedelta = timedelta(minutes=30)

    __query: str = None
    __ignoreCache: bool = False

    def __init__(self, query: str = None, ignoreCache: bool = False) -> None:
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
        req = Request("https://services.nvd.nist.gov/rest/json/cves/1.0",
                      params=args)
        json = req.json
        return self.tocache(CVEResponse.from_dict(json))

    @property
    def response(self) -> CVEResponse:
        isLoaded = self.load()
        if self.__ignoreCache or (not isLoaded):
            self._struct = self.fetch()
        return self._struct.struct

    @property
    def message(self) -> str:
        response: CVEResponse = self.response
        rows = [
            CVEHeader(cve.id, cve.description, cve.severity, cve.attackVector)
            for cve in response.result.CVE_Items
        ]
        TextOutput.addRows(rows)
        return TextOutput.render()

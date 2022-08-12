from enum import Enum
from urllib.parse import urlencode

class UrlBase(Enum):
    BASE_URL = "https://www.transfermarkt.co.uk"
    SEARCH_PLAYER = "/schnellsuche/ergebnis/schnellsuche"


class UrlMeta(type):

    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(
                UrlMeta, cls
            ).__call__(*args, **kwargs)
        return cls._instance


class Url(object, metaclass=UrlMeta):

    def getUrl(path: str, *args, **kwargs):
        query = urlencode(kwargs)
        return f"{UrlBase.BASE_URL.value}/{path}?{query}"
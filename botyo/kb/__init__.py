from hashlib import blake2b
import wikipedia
from wikipedia.exceptions import DisambiguationError
import logging
from typing import Optional
from cachable.request import Request
from botyo.chatyo import Response, getResponse, Payload
from botyo.core.store import RedisCachable
from pydantic import BaseModel


class KbStruct(BaseModel):
    summary: str
    content: str


class WikiSearchArguments(BaseModel):
    gsrsearch: str
    action: str = "query"
    origin: str = "*"
    format: str = "json"
    generator: str = "search"
    gsrnamespace: int = 0
    gsrlimit: int = 5


class PageItem(BaseModel):
    pageid: int
    ns: int
    title: str
    index: int


class QueryItem(BaseModel):
    pages: Optional[dict[str, PageItem]] = None


class QueryResponse(BaseModel):
    query: Optional[QueryItem] = None


class WikiApi:
    BASE = "https://en.wikipedia.org/w/api.php"


class KnowledgeBase(RedisCachable):

    __query = None
    __id = None
    _struct: Optional[KbStruct] = None

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__query = name

    def search(self) -> list[PageItem]:
        try:
            args = WikiSearchArguments(gsrsearch=self.__query)
            req = Request(WikiApi.BASE, params=args.model_dump())
            json = req.json
            response: QueryResponse = QueryResponse(**json)
            assert response.query
            assert response.query.pages
            return list(response.query.pages.values())
        except AssertionError:
            raise FileNotFoundError

    def generate(self) -> str:
        try:
            pages = self.search()
            first = next(filter(lambda x: x.index == 1, pages), None)
            assert first
            page = wikipedia.page(pageid=first.pageid)
            self._struct = KbStruct(
                summary=page.summary,
                content=page.content
            )
            return self.tocache(self._struct)
        except DisambiguationError as e:
            options = "\n".join(e.options)
            return f"Maybe you mean: {options}"
        except Exception as e:
            logging.exception(e)
            return ""

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__query.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def summary(self) -> Optional[str]:
        try:
            if not self.load():
                self.generate()
            assert self._struct
            return self._struct.summary
        except AssertionError:
            return None

    @property
    def content(self) -> Optional[str]:
        if not self.load():
            self.generate()
        assert self._struct
        return self._struct.content

    @classmethod
    def answer(cls, question) -> Response:
        return getResponse(
            "kb/ask",
            Payload(message=question)
        )

    @classmethod
    def summarized(cls, title: str) -> Response:
        return getResponse(
            "kb/tell",
            Payload(message=title)
        )

    @classmethod
    def wolfram(cls, question: str) -> Response:
        return getResponse(
            "kb/wtf",
            Payload(message=question)
        )

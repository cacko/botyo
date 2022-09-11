from dataclasses import dataclass
from hashlib import blake2b
from typing import Optional
from uuid import uuid1
import logging
from cachable.request import Request
from dataclasses_json import dataclass_json
from cachable.models import BinaryStruct
from cachable.cacheable import CachableFile
from app.demographics import Gender
from app.chatyo import getResponse, Payload

BASE_URL = "https://fakeface.rest/face/json"


@dataclass_json
@dataclass
class Query:
    gender: Optional[str] = None
    minimum_age: Optional[int] = 25
    maximum_age: Optional[int] = 70
    t: Optional[str] = None

    def __post_init__(self):
        self.t = uuid1().hex


class FakeFace(CachableFile):

    _struct: BinaryStruct = None
    __name = None
    __id = None
    __gender: Gender = None
    SIZE = (200, 200)

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__name = name

    def _init(self):
        if self.isCached:
            return
        try:
            gender = self.gender
            params = Query()
            if gender in [Gender.M, Gender.F]:
                params.gender = gender.value
            res = Request(BASE_URL, params=params.to_dict())
            json = res.json
            photo_url = json.get("image_url")
            res = Request(photo_url)
            self.tocache(res.binary)
        except Exception as e:
            logging.exception(e)
            pass

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def filename(self):
        return f"{self.id}.png"

    @property
    def gender(self) -> Gender:
        if not self.__gender:
            resp = getResponse(
                "name/gender", Payload(
                    message=self.__name,
                ))
            self.__gender = Gender(resp.response)
        return self.__gender

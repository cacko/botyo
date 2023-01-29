from dataclasses import dataclass
from hashlib import blake2b
from typing import Optional
from uuid import uuid1
import logging
from cachable.request import Request
from pydantic import BaseModel, Extra, Field
from cachable.models import BinaryStruct
from botyo.demographics import Gender
from botyo.chatyo import getResponse, Payload
from botyo.core.store import ImageCachable

BASE_URL = "https://fakeface.rest/face/json"


class Query(BaseModel, extra=Extra.ignore):
    gender: Optional[str] = None
    minimum_age: Optional[int] = Field(default=25)
    maximum_age: Optional[int] = Field(default=70)
    t: Optional[str] = None

    def __post_init__(self):
        self.t = uuid1().hex


class FakeFace(ImageCachable):

    _struct: Optional[BinaryStruct] = None
    __name: str
    __id: Optional[str] = None
    __gender: Optional[Gender] = None
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
            res = Request(BASE_URL, params=params.dict())
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
                "name/gender",
                Payload(
                    message=self.__name,
                ),
            )
            self.__gender = Gender(resp.response)
        return self.__gender

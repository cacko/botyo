from argparse import ArgumentParser
from botyo.core.config import Config as app_config
from typing import Optional
from enum import StrEnum
import requests
from pydantic import BaseModel, Field, Extra

from botyo.server.output import split_with_quotes


class CaptionParams(BaseModel, extra=Extra.ignore):
    template_id: int
    top_text: str
    bottom_text: str = Field(default="")


class CaptionResponseData(BaseModel, extra=Extra.ignore):
    url: str
    page_url: str


class CaptionResponse(BaseModel, extra=Extra.ignore):
    success: bool
    data: CaptionResponseData


class ENDPOINT(StrEnum):
    CAPTION = 'https://api.imgflip.com/caption_image'


class ImgFlipMeta(type):

    __instance: Optional['ImgFlip'] = None
    __caption_parser: Optional['ArgumentParser'] = None

    def __call__(cls, *args, **kwds):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    @property
    def caption_parser(cls) -> ArgumentParser:
        if not cls.__caption_parser:
            parser = ArgumentParser(
                description="Caption Generator",
                add_help=False,
                exit_on_error=False
            )
            parser.add_argument("template_id", type=int)
            parser.add_argument("-t",
                                "--top_text",
                                type=str)
            parser.add_argument("-b",
                                "--bottom_text",
                                type=str,
                                default="")
            cls.__caption_parser = parser
        return cls.__caption_parser

    def caption(cls, query: str) -> CaptionResponse:
        namespace, _ = cls.caption_parser.parse_known_args(split_with_quotes(query))
        params = CaptionParams(**namespace.__dict__)
        return cls().caption_image(params)


class ImgFlip(object, metaclass=ImgFlipMeta):

    def __init__(self):
        self.__config = app_config.imgflip

    def caption_image(self, params: CaptionParams):
        template_id = params.template_id
        top = params.top_text
        bottom = params.bottom_text
        payload = {
            'username': self.__config.username,
            'password': self.__config.password,
            'template_id': template_id,
            'text0': top,
            'text1': bottom
        }
        response = requests.post(
            ENDPOINT.CAPTION.value,
            params=payload
        ).json()
        return CaptionResponse(**response)

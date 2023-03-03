from argparse import ArgumentParser
import logging
from botyo.core.config import Config as app_config
from typing import Optional
from enum import StrEnum, IntEnum
import requests
from pydantic import BaseModel, Extra
from random import choice
import pandas as pd
from shlex import split


class Templates(IntEnum):
    BART = 445427161
    XAVIER = 445429370


def get_top_templates() -> list[int]:
    url = 'https://imgflip.com/popular-meme-ids'
    res = requests.get(url)
    html = res.content
    df = pd.read_html(
        str(html),
        match="Alternate Names",
        skiprows=[0]
    )[0]
    df.columns = ['ID', 'Name', 'Junk']
    return [int(r['ID'])for _, r in df.iterrows()]


class CaptionParams(BaseModel, extra=Extra.ignore):
    top_text: list[str]
    bottom_text: list[str]
    template_id: Optional[int] = None

    def __init__(self, **data):
        try:
            tpl_id = data.get("template_id")
            assert isinstance(tpl_id, str)
            if not tpl_id.isnumeric():
                tpl = Templates[tpl_id.upper()]
                data["template_id"] = tpl.value
        except AssertionError:
            pass
        except KeyError:
            data["template_id"] = 0
        super().__init__(**data)


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
            parser.add_argument("top_text", type=str, nargs='+')
            parser.add_argument("-t",
                                "--template_id",
                                type=str, default=0)
            parser.add_argument("-b",
                                "--bottom_text",
                                type=str, default=[""], nargs="*")
            cls.__caption_parser = parser
        return cls.__caption_parser

    def caption(cls, query: str) -> CaptionResponse:
        arg_line = f"{query}".replace("'", "\\'")
        logging.warning(split(arg_line))
        namespace, _ = cls.caption_parser.parse_known_args(split(arg_line))
        params = CaptionParams(**namespace.__dict__)
        return cls().caption_image(params)


class ImgFlip(object, metaclass=ImgFlipMeta):

    def __init__(self):
        self.__config = app_config.imgflip

    def caption_image(self, params: CaptionParams):
        template_id = params.template_id
        if not template_id:
            template_id = choice(get_top_templates())
        top = " ".join(params.top_text)
        bottom = " ".join(params.bottom_text)
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

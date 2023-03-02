from argparse import ArgumentParser
from botyo.core.config import Config as app_config
from typing import Optional
from enum import StrEnum
import requests
from pydantic import BaseModel, Field, Extra
from random import choice

from botyo.server.output import split_with_quotes

TOP_TEMPLATES = [
    112126428,
    87743020,
    438680,
    129242436,
    124822590,
    217743513,
    131087935,
    61579,
    93895088,
    102156234,
    4087833,
    1035805,
    101470,
    91538330,
    188390779,
    247375501,
    89370399,
    97984,
    61520,
    119139145,
    131940431,
    222403160,
    114585149,
    155067746,
    5496396,
    178591752,
    61532,
    123999232,
    21735,
    8072285,
    100777631,
    27813981,
    61585,
    226297822,
    124055727,
    28251713,
    135256802,
    61539,
    148909805,
    134797956,
    101288,
    80707627,
    252600902,
    6235864,
    61527,
    61556,
    175540452,
    161865971,
    91545132,
    563423,
    180190441,
    61546,
    84341851,
    61582,
    405658,
    61533,
    14371066,
    16464531,
    135678846,
    101511,
    110163934,
    61544,
    3218037,
    1509839,
    196652226,
    101287,
    235589,
    55311130,
    100947,
    79132341,
    61516,
    132769734,
    195515965,
    14230520,
    245898,
    101440,
    922147,
    99683372,
    61580,
    101910402,
    259237855,
    101716,
    40945639,
    259680,
    109765,
    9440985,
    61581,
    56225174,
    12403754,
    163573,
    21604248,
    460541,
    195389,
    100955,
    29617627,
    444501,
    766986,
    1367068,
    6531067
]


class CaptionParams(BaseModel, extra=Extra.ignore):
    top_text: str
    bottom_text: str = Field(default="")
    template_id: Optional[int] = None


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
            parser.add_argument("top_text", type=str)
            parser.add_argument("-t",
                                "--top_text",
                                type=int)
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
        if not template_id:
            template_id = choice(TOP_TEMPLATES)
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

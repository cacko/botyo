from pathlib import Path
from xml.dom import ValidationErr

from botyo.server.models import Attachment, ApiError
from cachable.request import Request, Method
from cachable.storage.file import FileStorage
from botyo.core.config import Config
from uuid import uuid4
import filetype
from enum import Enum
from botyo.server.output import TextOutput
from emoji import emojize
from botyo.image.models import (
    AnalyzeReponse,
    Upload2Wallies
)
from typing import Optional
from argparse import ArgumentParser, ArgumentError
from pydantic import BaseModel, Field, validator
from corestring import split_with_quotes, string_hash
from requests.exceptions import JSONDecodeError
import logging
from functools import reduce
import json


class ImageGeneratorParams(BaseModel):
    prompt: list[str]
    height: Optional[int] = None
    width: Optional[int] = None
    guidance_scale: Optional[float] = None
    image_guidance_scale: Optional[float] = None
    num_inference_steps: Optional[int] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    upscale: int = Field(default=0)
    auto_prompt: Optional[str] = None
    model: str = Field(default="default")
    aspect_ratio: Optional[str] = None
    editing_prompt: Optional[list[str]] = None

    @validator("prompt")
    def static_prompt(cls, prompt: list[str]):
        return " ".join(prompt)

    @validator("upscale")
    def static_upscale(cls, upscale: Optional[bool] = None):
        if not upscale:
            return 0
        return 1


class VariationGeneratorParams(BaseModel):
    guidance_scale: Optional[float] = Field(default=7)
    num_inference_steps: Optional[int] = Field(default=50)
    num_images_per_prompt: Optional[int] = Field(default=1)


class Action(Enum):
    ANALYZE = "face/analyze"
    TAG = "face/tag"
    HOWCUTE = "face/howcute"
    CLASSIFY = "image/classify"
    PIXEL = "image/pixel"
    VARIATION = "image/variation"
    TXT2IMG = "image/txt2img"
    IMG2IMG = "image/img2img"
    PIX2PIX = "image/pix2pix"
    GPS2IMG = "image/gps2img"
    UPLOAD2WALLIES = "image/upload2wallies"
    RANDOMCUTENESS = "images/rndcnt"
    OPTIONS = "image/options"


class ImageOptions(BaseModel):
    model: list[str]
    resolution: list[str]
    category: list[str]


class ImageMeta(type):

    __image_generator_parser: Optional[ArgumentParser] = None
    __variation_generator_parser: Optional[ArgumentParser] = None
    __options: Optional[ImageOptions] = None
    __is_admin: bool = False

    def __call__(cls, attachment: Optional[Attachment] = None, *args, **kwds):
        return type.__call__(cls, attachment=attachment, *args, **kwds)

    def tag(cls, attachment: Attachment) -> tuple[Attachment, str]:
        return cls(attachment).do_tag()

    def analyze(cls, attachment: Attachment) -> tuple[Attachment, str]:
        return cls(attachment).do_analyze()

    def howcute(cls, attachment: Attachment) -> tuple[Attachment, str]:
        return cls(attachment).do_howcute()

    def classify(cls, attachment: Attachment) -> tuple[Attachment, dict]:
        return cls(attachment).do_classify()

    def pixel(
            cls,
            attachment: Attachment,
            block_size: int = 8
    ) -> tuple[Attachment, dict]:
        return cls(attachment).do_pixel(block_size)

    @property
    def is_admin(cls) -> bool:
        return cls.__is_admin

    @is_admin.setter
    def is_admin(cls, val: bool):
        cls.__is_admin = val

    @property
    def options(cls) -> ImageOptions:
        if not cls.__options:
            rs = Request(f"{Config.image.base_url}/{Action.OPTIONS.value}")
            json_data = rs.json
            assert json_data
            cls.__options = ImageOptions(**json_data)
        return cls.__options

    @property
    def variation_generator_parser(cls) -> ArgumentParser:
        if not cls.__variation_generator_parser:
            parser = ArgumentParser(
                description="Variation Generator",
                add_help=False,
                exit_on_error=False
            )
            parser.add_argument("-n",
                                "--num_images_per_prompt",
                                type=int)
            parser.add_argument("-g",
                                "--guidance_scale",
                                type=float)
            parser.add_argument("-s",
                                "--num_inference_steps",
                                type=int)
            cls.__variation_generator_parser = parser
        return cls.__variation_generator_parser

    def variation_generator_params(cls,
                                   prompt: str) -> VariationGeneratorParams:
        parser = cls.variation_generator_parser
        namespace, _ = parser.parse_known_args(split_with_quotes(prompt))
        return VariationGeneratorParams(**namespace.__dict__)

    @ property
    def image_generator_parser(cls) -> ArgumentParser:
        if not cls.__image_generator_parser:
            parser = ArgumentParser(description="Image Processing",
                                    exit_on_error=False)
            parser.add_argument("prompt", nargs="*")
            parser.add_argument("-n",
                                "--negative_prompt",
                                type=str)
            parser.add_argument("-g",
                                "--guidance_scale",
                                type=float)
            parser.add_argument("-k",
                                "--image_guidance_scale",
                                type=float)
            parser.add_argument("-i", "--num_inference_steps", type=int)
            parser.add_argument("-s", "--seed", type=int)
            parser.add_argument(
                "-m",
                "--model",
                choices=cls.options.model,
                default="default"
            )
            parser.add_argument("-u", "--upscale", action="store_true")
            parser.add_argument("-a", "--auto_prompt", type=int)
            parser.add_argument(
                "-r",
                "--aspect-ratio",
                choices=cls.options.resolution
            )
            parser.add_argument("-e", "--editing_prompt", action="append", type=str)
            cls.__image_generator_parser = parser
        return cls.__image_generator_parser

    def image_generator_params(
        cls,
        prompt: Optional[str]
    ) -> ImageGeneratorParams:
        parser = cls.image_generator_parser
        if not prompt:
            return ImageGeneratorParams(prompt=[""])
        namespace, _ = parser.parse_known_args(
            split_with_quotes(prompt.replace("\u8192", '--'))
        )
        return ImageGeneratorParams(**namespace.__dict__)

    def variation(
        cls,
        attachment: Attachment,
        prompt: Optional[str] = None
    ) -> tuple[Attachment, str]:
        return cls(attachment).do_variation(prompt)

    def txt2img(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_txt2img(prompt)

    def img2img(
        cls,
        attachment: Attachment,
        prompt: Optional[str] = None
    ) -> tuple[Attachment, str]:
        return cls(attachment).do_img2img(prompt)

    def pix2pix(
        cls,
        attachment: Attachment,
        prompt: Optional[str] = None
    ) -> tuple[Attachment, str]:
        return cls(attachment).do_pix2pix(prompt)

    def upload2wallies(
        cls,
        params: Upload2Wallies
    ) -> str:
        return cls().do_upload2wallies(params)

    def gps2img(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_gps2img(prompt)

    def random_cuteness(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_random_cuteness(prompt)


class Image(object, metaclass=ImageMeta):

    __attachment: Optional[Attachment] = None

    def __init__(self, attachment: Optional[Attachment] = None) -> None:
        self.__attachment = attachment

    def do_analyze(self):
        attachment, message = self.getResponse(Action.ANALYZE)
        if message:
            data = json.loads(message) if isinstance(message, str) else message
            analyses = AnalyzeReponse(**data)
            rows = [
                ["Age: ", analyses.age],
                [
                    "Emotion: ",
                    analyses.dominant_emotion,
                    emojize(analyses.emotion_icon),
                ],
                [
                    "Race: ", analyses.dominant_race,
                    emojize(analyses.race_icon)
                ],
                ["Gender: ", analyses.dominant_gender,
                 emojize(analyses.gender_icon)],
            ]
            TextOutput.addRows(["".join(map(str, row)) for row in rows])
            message = TextOutput.render()
        return attachment, message

    def do_tag(self):
        return self.getResponse(Action.TAG)

    def do_howcute(self):
        return self.getResponse(Action.HOWCUTE)

    def do_classify(self):
        return self.getResponse(Action.CLASSIFY)

    def do_pixel(self, block_size):
        return self.getResponse(Action.PIXEL, block_size)

    def do_variation(self, prompt: Optional[str] = None):
        try:
            assert prompt
            params = Image.variation_generator_params(prompt)
            return self.getResponse(
                Action.VARIATION,
                uuid4().hex,
                json=params.dict()
            )
        except AssertionError:
            return self.getResponse(
                Action.VARIATION,
                uuid4().hex,
                json=VariationGeneratorParams().dict()
            )

    def do_txt2img(
        self,
        prompt: str,
        action: Action = Action.TXT2IMG
    ):
        try:
            params = Image.image_generator_params(prompt)
            logging.info(params)
            return self.getResponse(
                action=action,
                action_param=string_hash(params.prompt),
                json=params.dict()
            )
        except (ValidationErr, ArgumentError) as e:
            logging.error(e)
            raise ApiError(f"{e}")

    def do_gps2img(self, prompt: str):
        try:
            params = Image.image_generator_params(prompt)
            return self.getResponse(Action.GPS2IMG,
                                    params.prompt,
                                    json=params.dict())
        except (ValidationErr, ArgumentError) as e:
            raise ApiError(f"{e}")

    def do_img2img(self, prompt: Optional[str] = None):

        params = Image.image_generator_params(prompt)
        return self.getResponse(Action.IMG2IMG,
                                params.prompt,
                                json=params.dict())

    def do_pix2pix(self, prompt: Optional[str] = None):
        logging.info(prompt)
        params = Image.image_generator_params(prompt)
        logging.info(params)
        return self.getResponse(Action.PIX2PIX,
                                params.prompt,
                                json=params.dict())

    def do_random_cuteness(self, prompt: str):
        return self.getResponse(
            Action.RANDOMCUTENESS,
            action_param=prompt,
        )

    def do_upload2wallies(
        self,
        params: Upload2Wallies,
    ):
        try:
            logging.info(params)
            ip = Path(params.image_url)
            _, message = self.getResponse(
                action=Action.UPLOAD2WALLIES,
                action_param=ip.name,
                json=params.dict()
            )
            return message
        except (ValidationErr, ArgumentError) as e:
            raise ApiError(f"{e}")

    def __make_request(self, path: str, json: dict = {}):
        attachment = self.__attachment
        params: dict = {}

        if attachment:
            assert isinstance(attachment, dict)
            p = Path(attachment.get("path", ""))
            kind = filetype.guess(p.as_posix())
            mime = attachment.get("contentType")
            fp = p.open("rb")
            assert kind
            params["files"] = {
                "file": (f"{p.name}.{kind.extension}", fp, mime, {
                    "Expires": "0"
                })
            }
            params["data"] = reduce(
                lambda r, x: {
                    **r,
                    **({
                        x: json.get(x)
                    } if json.get(x, None) else {})
                }, json.keys(), {})
            logging.debug(params["data"])
        else:
            params["json"] = reduce(
                lambda r, x: {
                    **r,
                    **({
                        x: json.get(x)
                    } if json.get(x, None) else {})
                }, json.keys(), {})
            logging.debug(params["json"])

        extra_headers = {}
        if self.__class__.is_admin:
            extra_headers["X-SuperUser"] = "1"

        return Request(
            f"{Config.image.base_url}/{path}",
            method=Method.POST,
            extra_headers=extra_headers,
            **params
        )

    def getResponse(self,
                    action: Action,
                    action_param=None,
                    json: dict = {}):
        path = action.value
        if action_param:
            path = f"{path}/{action_param}"
        req = self.__make_request(path=path, json=json)
        # if req.status > 400:
        #     raise ApiError("Error")
        message = ""
        attachment = None
        is_multipart = req.is_multipart
        if is_multipart:
            multipart = req.multipart
            cp = FileStorage.storage_path
            for part in multipart.parts:
                content_type = part.headers.get(
                    b"content-type",  # type: ignore
                    b""  # type: ignore
                ).decode()
                if "image/png" in content_type:
                    fp = cp / f"{uuid4().hex}.png"
                    fp.write_bytes(part.content)
                    attachment = Attachment(
                        path=fp.absolute().as_posix(),
                        contentType="image/png",
                    )
                elif "image/jpeg" in content_type:
                    fp = cp / f"{uuid4().hex}.jpg"
                    fp.write_bytes(part.content)
                    attachment = Attachment(
                        path=fp.absolute().as_posix(),
                        contentType="image/jpeg",
                    )
                elif "image/webp" in content_type:
                    fp = cp / f"{uuid4().hex}.webp"
                    fp.write_bytes(part.content)
                    attachment = Attachment(
                        path=fp.absolute().as_posix(),
                        contentType="image/webp",
                    )
                else:
                    message = part.text
        else:
            try:
                message = req.json
            except JSONDecodeError as e:
                logging.error(e)
                raise ApiError(f"{e}")
        return attachment, message

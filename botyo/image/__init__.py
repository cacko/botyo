from pathlib import Path
from xml.dom import ValidationErr
from requests import JSONDecodeError
from botyo.api.console.geo import GeoLocation
from botyo.core import normalize_prompt
from botyo.server.models import Attachment, ApiError
from cachable.request import Request, Method
from cachable.storage.file import FileStorage
from botyo.core.config import Config
from uuid import uuid4
import filetype
from enum import Enum
from botyo.server.output import TextOutput
from emoji import emojize
from botyo.image.models import AnalyzeReponse, Upload2Wallies
from typing import Optional
from argparse import ArgumentParser, ArgumentError
from pydantic import BaseModel, Field, validator
from corestring import split_with_quotes, string_hash
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
    model: Optional[str] = None
    aspect_ratio: Optional[str] = None
    editing_prompt: Optional[list[str]] = None
    template: Optional[str] = None

    @validator("prompt")
    def static_prompt(cls, prompt: list[str]):
        return " ".join(prompt)

    @validator("upscale")
    def static_upscale(cls, upscale: Optional[bool] = None):
        if not upscale:
            return 0
        return 1


class Image2GeneratorParams(BaseModel):
    prompt: Optional[str] = None
    guidance_scale: Optional[float] = None
    num_inference_steps: Optional[int] = None
    negative_prompt: Optional[str] = None
    strength: Optional[float] = None
    upscale: int = Field(default=2)
    model: Optional[str] = None
    template: Optional[str] = None


class QRGeneratorParams(BaseModel):
    code: list[str]
    prompt: Optional[str] = None
    guidance_scale: Optional[float] = None
    condition_scale: Optional[float] = None
    num_inference_steps: Optional[int] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    auto_prompt: Optional[str] = None
    model: Optional[str] = None

    @validator("code")
    def static_code(cls, code: list[str]):
        return " ".join(code)


class VariationGeneratorParams(BaseModel):
    guidance_scale: Optional[float] = Field(default=7)
    num_inference_steps: Optional[int] = Field(default=50)
    num_images_per_prompt: Optional[int] = Field(default=1)


class StreetViewGeneratorParams(BaseModel):
    query: list[str]
    style: Optional[str] = None


class Action(Enum):
    ANALYZE = "face/analyze"
    TAG = "face/tag"
    HOWCUTE = "image/howcute"
    CLASSIFY = "image/classify"
    PIXEL = "image/pixel"
    VARIATION = "image/variation"
    TXT2IMG = "image/txt2img"
    QR2IMG = "image/qr2img"
    STREETVIEW = "image/streetview"
    UPLOAD2WALLIES = "image/upload2wallies"
    OPTIONS = "image/options"
    IMG2IMG = "image/img2img"


class ImageOptions(BaseModel):
    model: list[str]
    resolution: list[str]
    category: list[str]
    template: list[str]
    qrcode: list[str]
    styles: list[str]


class ImageMeta(type):
    __image_generator_parser: Optional[ArgumentParser] = None
    __image2_generator_parser: Optional[ArgumentParser] = None
    __variation_generator_parser: Optional[ArgumentParser] = None
    __qr_generator_parser: Optional[ArgumentParser] = None
    __street_generator_parser: Optional[ArgumentParser] = None
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
        cls, attachment: Attachment, block_size: int = 8
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
                description="Variation Generator", add_help=False, exit_on_error=False
            )
            parser.add_argument("-n", "--num_images_per_prompt", type=int)
            parser.add_argument("-g", "--guidance_scale", type=float)
            parser.add_argument("-s", "--num_inference_steps", type=int)
            cls.__variation_generator_parser = parser
        return cls.__variation_generator_parser

    def variation_generator_params(cls, prompt: str) -> VariationGeneratorParams:
        parser = cls.variation_generator_parser
        namespace, _ = parser.parse_known_args(split_with_quotes(prompt))
        return VariationGeneratorParams(**namespace.__dict__)

    @property
    def image_generator_parser(cls) -> ArgumentParser:
        if not cls.__image_generator_parser:
            parser = ArgumentParser(description="Image Processing", exit_on_error=False)
            parser.add_argument("prompt", nargs="*")
            parser.add_argument("-n", "--negative_prompt", type=str)
            parser.add_argument("-g", "--guidance_scale", type=float)
            parser.add_argument("-k", "--image_guidance_scale", type=float)
            parser.add_argument("-i", "--num_inference_steps", type=int)
            parser.add_argument("-s", "--seed", type=int)
            parser.add_argument("-m", "--model", choices=cls.options.model)
            parser.add_argument("-u", "--upscale", action="store_true")
            parser.add_argument("-a", "--auto_prompt", type=int)
            parser.add_argument("-r", "--aspect-ratio", choices=cls.options.resolution)
            parser.add_argument("-e", "--editing_prompt", action="append", type=str)
            parser.add_argument("-t", "--template", choices=cls.options.template)
            cls.__image_generator_parser = parser
        return cls.__image_generator_parser

    def image_generator_params(cls, prompt: Optional[str]) -> ImageGeneratorParams:
        parser = cls.image_generator_parser
        if not prompt:
            return ImageGeneratorParams(prompt=[""])
        namespace, _ = parser.parse_known_args(
            split_with_quotes(normalize_prompt(prompt))
        )
        return ImageGeneratorParams(**namespace.__dict__)

    @property
    def image2_generator_parser(cls) -> ArgumentParser:
        if not cls.__image2_generator_parser:
            parser = ArgumentParser(description="Image Processing", exit_on_error=False)
            parser.add_argument("-p", "--prompt")
            parser.add_argument("-n", "--negative_prompt", type=str)
            parser.add_argument("-g", "--guidance_scale", type=float)
            parser.add_argument("-i", "--num_inference_steps", type=int)
            parser.add_argument("-s", "--strength", type=float)
            parser.add_argument("-m", "--model", choices=cls.options.model)
            parser.add_argument("-u", "--upscale", action="store_true")
            parser.add_argument("-t", "--template", choices=cls.options.styles)
            cls.__image2_generator_parser = parser
        return cls.__image2_generator_parser

    def image2_generator_params(cls, prompt: Optional[str]) -> Image2GeneratorParams:
        parser = cls.image2_generator_parser
        if not prompt:
            return Image2GeneratorParams()
        namespace, _ = parser.parse_known_args(
            split_with_quotes(normalize_prompt(prompt))
        )
        return Image2GeneratorParams(**namespace.__dict__)

    @property
    def qrgenerator_parser(cls) -> ArgumentParser:
        if not cls.__qr_generator_parser:
            parser = ArgumentParser(description="QR Processing", exit_on_error=False)
            parser.add_argument("code", nargs="+")
            parser.add_argument("-p", "--prompt", type=str)
            parser.add_argument("-n", "--negative_prompt", type=str)
            parser.add_argument("-g", "--guidance_scale", type=float)
            parser.add_argument("-c", "--controlnet_conditioning_scale", type=float)
            parser.add_argument("-i", "--num_inference_steps", type=int)
            parser.add_argument("-s", "--seed", type=int)
            parser.add_argument(
                "-m", "--model", choices=cls.options.qrcode, default="default"
            )
            parser.add_argument("-a", "--auto_prompt", type=int)
            cls.__qr_generator_parser = parser
        return cls.__qr_generator_parser

    def qr_generator_params(cls, prompt: Optional[str]) -> QRGeneratorParams:
        parser = cls.qrgenerator_parser
        if not prompt:
            return QRGeneratorParams(code=[""])
        namespace, _ = parser.parse_known_args(
            split_with_quotes(normalize_prompt(prompt))
        )
        return QRGeneratorParams(**namespace.__dict__)

    @property
    def streetgenerator_parser(cls) -> ArgumentParser:
        if not cls.__street_generator_parser:
            parser = ArgumentParser(description="QR Processing", exit_on_error=False)
            parser.add_argument("query", nargs="+")
            parser.add_argument("-s", "--style", choices=cls.options.styles)
            cls.__street_generator_parser = parser
        return cls.__street_generator_parser

    def street_generator_params(
        cls, prompt: Optional[str]
    ) -> StreetViewGeneratorParams:
        parser = cls.streetgenerator_parser
        if not prompt:
            return StreetViewGeneratorParams(query=[""])
        namespace, _ = parser.parse_known_args(
            split_with_quotes(normalize_prompt(prompt))
        )

        return StreetViewGeneratorParams(**namespace.__dict__)

    def variation(
        cls, attachment: Attachment, prompt: Optional[str] = None
    ) -> tuple[Attachment, str]:
        return cls(attachment).do_variation(prompt)

    def img2img(cls, attachment: Attachment, prompt: str) -> tuple[Attachment, str]:
        return cls(attachment).do_img2img(prompt)

    def txt2img(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_txt2img(prompt)

    def qr2img(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_qr2img(prompt)

    def upload2wallies(cls, params: Upload2Wallies) -> str:
        return cls().do_upload2wallies(params)

    def streetview(cls, location: GeoLocation, style: str) -> tuple[Attachment, str]:
        return cls().do_streetview(location, style)


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
                ["Race: ", analyses.dominant_race, emojize(analyses.race_icon)],
                ["Gender: ", analyses.dominant_gender, emojize(analyses.gender_icon)],
            ]
            TextOutput.addRows(["".join(map(str, row)) for row in rows])
            message = TextOutput.render()
        return attachment, message

    def do_tag(self):
        return self.getResponse(Action.TAG)

    def do_howcute(self):
        return self.getResponse(Action.HOWCUTE)

    def do_classify(self):
        return self.getResponse(Action.CLASSIFY, uuid4().hex)

    def do_pixel(self, block_size):
        return self.getResponse(Action.PIXEL, block_size)

    def do_variation(self, prompt: Optional[str] = None):
        try:
            assert prompt
            params = Image.variation_generator_params(prompt)
            return self.getResponse(
                Action.VARIATION, uuid4().hex, json_data=params.model_dump()
            )
        except AssertionError as e:
            logging.info(e)
            return self.getResponse(
                Action.VARIATION,
                uuid4().hex,
                json_data=VariationGeneratorParams().model_dump(),
            )

    def do_img2img(self, prompt: Optional[str] = None):
        try:
            params = Image.image2_generator_params(prompt)
            return self.getResponse(
                Action.IMG2IMG, uuid4().hex, json_data=params.model_dump()
            )
        except (ValidationErr, ArgumentError) as e:
            logging.error(e)
            raise ApiError(f"{e}")

    def do_txt2img(self, prompt: str, action: Action = Action.TXT2IMG):
        try:
            params = Image.image_generator_params(prompt)
            logging.info(params)
            return self.getResponse(
                action=action,
                action_param=string_hash(params.prompt),
                json_data=params.model_dump(),
            )
        except AssertionError as e:
            logging.info(e)
            return self.getResponse(
                action=action,
                action_param=uuid4().hex,
                json_data=Image2GeneratorParams().model_dump(),
            )

    def do_qr2img(self, prompt: str, action: Action = Action.QR2IMG):
        try:
            params = Image.qr_generator_params(prompt)
            logging.info(params)
            return self.getResponse(
                action=action,
                action_param=string_hash(params.code),
                json_data=params.model_dump(),
            )
        except (ValidationErr, ArgumentError) as e:
            logging.exception(e)
            raise ApiError(f"{e}")

    def do_streetview(self, location: GeoLocation, style: str):
        try:
            gps_part = ",".join(map(str, location.location))
            return self.getResponse(
                Action.STREETVIEW, action_param=f"{style}/{gps_part}", method=Method.GET
            )
        except (ValidationErr, ArgumentError) as e:
            raise ApiError(f"{e}")

    def do_upload2wallies(
        self,
        params: Upload2Wallies,
    ):
        try:
            logging.debug(params)
            ip = Path(params.image_url)
            _, message = self.getResponse(
                action=Action.UPLOAD2WALLIES,
                action_param=ip.name,
                json_data=params.model_dump(),
            )
            return message
        except (ValidationErr, ArgumentError) as e:
            raise ApiError(f"{e}")

    def __make_request(
        self, path: str, json_data: dict = {}, method: Method = Method.POST
    ):
        attachment = self.__attachment
        params: dict = {}
        logging.debug(self.__attachment)
        if attachment:
            p = Path(attachment.path)
            kind = filetype.guess(p.as_posix())
            mime = attachment.contentType
            fp = p.open("rb")
            assert kind
            params["files"] = {
                "file": (f"{p.name}.{kind.extension}", fp, mime, {"Expires": "0"})
            }
            form_data = reduce(
                lambda r, x: {
                    **r,
                    **({x: json_data.get(x)} if json_data.get(x, None) else {}),
                },
                json_data.keys(),
                {},
            )
            params["data"] = {**form_data, "data": json.dumps(form_data)}
            logging.debug(params)
        else:
            params["json"] = reduce(
                lambda r, x: {
                    **r,
                    **({x: json_data.get(x)} if json_data.get(x, None) else {}),
                },
                json_data.keys(),
                {},
            )
            logging.debug(params["json"])

        extra_headers = {}
        if self.__class__.is_admin:
            extra_headers["X-SuperUser"] = "1"

        return Request(
            f"{Config.image.base_url}/{path}",
            method=method,
            extra_headers=extra_headers,
            **params,
        )

    def getResponse(
        self,
        action: Action,
        action_param=None,
        json_data: dict = {},
        method=Method.POST,
    ):
        path = action.value
        if action_param:
            path = f"{path}/{action_param}"
        req = self.__make_request(path=path, json_data=json_data, method=method)
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
                    b"",  # type: ignore
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

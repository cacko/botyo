from pathlib import Path
from botyo.server.models import Attachment
from cachable.request import Request, Method
from cachable.storage.file import FileStorage
from botyo.core.config import Config
from uuid import uuid4
import filetype
from enum import Enum
from botyo.server.output import TextOutput
from emoji import emojize
from botyo.image.models import AnalyzeReponse
from typing import Optional
from argparse import ArgumentParser, ArgumentError
from pydantic import BaseModel, Field
from corestring import split_with_quotes
from requests.exceptions import JSONDecodeError
import logging
from functools import reduce


class ImageGeneratorParams(BaseModel):
    prompt: str
    height: int = Field(default=512)
    width: int = Field(default=512)
    guidance_scale: float = Field(default=7)
    num_inference_steps: int = Field(default=30)
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    upscale: int = Field(default=0)
    model: str = Field(default="default")


class VariationGeneratorParams(BaseModel):
    guidance_scale: float = Field(default=7)
    num_inference_steps: int = Field(default=30)
    num_images_per_prompt: int = Field(default=1)


class Action(Enum):
    ANALYZE = "face/analyze"
    TAG = "face/tag"
    HOWCUTE = "face/howcute"
    CLASSIFY = "image/classify"
    PIXEL = "image/pixel"
    POLYGON = "image/polygon"
    VARIATION = "image/variation"
    TXT2IMG = "image/txt2img"
    IMG2IMG = "image/img2img"
    PORTRAIT = "image/txt2portrait"
    GPS2IMG = "image/gps2img"


class ImageMeta(type):

    __image_generator_parser: Optional[ArgumentParser] = None
    __variation_generator_parser: Optional[ArgumentParser] = None

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

    def pixel(cls,
              attachment: Attachment,
              block_size: int = 8) -> tuple[Attachment, dict]:
        return cls(attachment).do_pixel(block_size)

    def polygon(cls,
                attachment: Attachment,
                frequency: int = 800) -> tuple[Attachment, dict]:
        return cls(attachment).do_polygon(frequency)

    @property
    def variation_generator_parser(cls) -> ArgumentParser:
        if not cls.__variation_generator_parser:
            parser = ArgumentParser(description="Variation Generator",
                                    add_help=False,
                                    exit_on_error=False)
            parser.add_argument("-n",
                                "--num_images_per_prompt",
                                type=int,
                                default=1)
            parser.add_argument("-g",
                                "--guidance_scale",
                                type=float,
                                default=3)
            parser.add_argument("-s",
                                "--num_inference_steps",
                                type=int,
                                default=30)
            cls.__variation_generator_parser = parser
        return cls.__variation_generator_parser

    def variation_generator_params(cls,
                                   prompt: str) -> VariationGeneratorParams:
        parser = cls.variation_generator_parser
        parsed = parser.parse_args(split_with_quotes(prompt))
        return VariationGeneratorParams(
            guidance_scale=parsed.guidance_scale,
            num_images_per_prompt=parsed.num_images_per_prompt,
            num_inference_steps=parsed.num_inference_steps,
        )

    @property
    def image_generator_parser(cls) -> ArgumentParser:
        if not cls.__image_generator_parser:
            parser = ArgumentParser(description="Image Processing",
                                    add_help=False,
                                    exit_on_error=False)
            parser.add_argument("prompt", nargs="+")
            parser.add_argument("-n",
                                "--negative_prompt",
                                type=str,
                                default="")
            parser.add_argument("-h", "--height", type=int, default=512)
            parser.add_argument("-w", "--width", type=int, default=512)
            parser.add_argument("-g",
                                "--guidance_scale",
                                type=float,
                                default=7)
            parser.add_argument("-i", "--num_inference_steps", default=30)
            parser.add_argument("-s", "--seed", type=int)
            parser.add_argument("-m", "--model", default="default")
            parser.add_argument("-u", "--upscale", action="store_true")
            cls.__image_generator_parser = parser
        return cls.__image_generator_parser

    def image_generator_params(cls,
                               prompt: Optional[str]) -> ImageGeneratorParams:
        parser = cls.image_generator_parser
        if not prompt:
            return ImageGeneratorParams(prompt="")
        namespace, _ = parser.parse_known_args(split_with_quotes(prompt))
        return ImageGeneratorParams(**namespace.__dict__)

    def variation(cls,
                  attachment: Attachment,
                  prompt: Optional[str] = None) -> tuple[Attachment, dict]:
        return cls(attachment).do_variation(prompt)

    def txt2img(cls, prompt: str) -> tuple[Attachment, dict]:
        return cls().do_txt2img(prompt)

    def txt2portrait(cls, prompt: str) -> tuple[Attachment, dict]:
        return cls().do_portrait(prompt)

    def img2img(cls,
                attachment: Attachment,
                prompt: Optional[str] = None) -> tuple[Attachment, dict]:
        return cls(attachment).do_img2img(prompt)

    def gps2img(cls, prompt: str) -> tuple[Attachment, str]:
        return cls().do_gps2img(prompt)


class Image(object, metaclass=ImageMeta):

    __attachment: Optional[Attachment] = None

    def __init__(self, attachment: Optional[Attachment] = None) -> None:
        self.__attachment = attachment

    def do_analyze(self):
        attachment, message = self.getResponse(Action.ANALYZE)
        if message:
            analyses = AnalyzeReponse(**message)
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
                ["Gender: ", analyses.gender,
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

    def do_polygon(self, frequency):
        return self.getResponse(Action.POLYGON, frequency)

    def do_variation(self, prompt: Optional[str] = None):
        assert prompt
        params = Image.variation_generator_params(prompt)
        return self.getResponse(Action.VARIATION,
                                uuid4().hex,
                                json=params.dict())

    def do_txt2img(self, prompt: str):
        try:
            params = Image.image_generator_params(prompt)

            return self.getResponse(Action.TXT2IMG,
                                    params.prompt,
                                    json=params.dict())
        except ArgumentError as e:
            raise AssertionError(e.message)

    def do_gps2img(self, prompt: str):
        try:
            params = Image.image_generator_params(prompt)
            return self.getResponse(Action.GPS2IMG,
                                    params.prompt,
                                    json=params.dict())
        except ArgumentError as e:
            raise AssertionError(e.message)

    def do_portrait(self, prompt: str):
        try:
            params = Image.image_generator_params(prompt)
            return self.getResponse(Action.PORTRAIT,
                                    params.prompt,
                                    json=params.dict())
        except ArgumentError as e:
            raise AssertionError(e.message)

    def do_img2img(self, prompt: Optional[str] = None):

        params = Image.image_generator_params(prompt)
        return self.getResponse(Action.IMG2IMG,
                                params.prompt,
                                json=params.dict())

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
                    x: json.get("x")
                } if json.get("x", None) else {})
            }, json.keys(), {})
        logging.debug(params["data"])

        return Request(f"{Config.image.base_url}/{path}",
                       method=Method.POST,
                       **params)

    def getResponse(self,
                    action: Action,
                    action_param=None,
                    json: dict = {}):
        path = action.value
        if action_param:
            path = f"{path}/{action_param}"
        req = self.__make_request(path=path, json=json)
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
                else:
                    message = part.text
        else:
            try:
                message = req.json
            except JSONDecodeError as e:
                logging.error(e)
                raise AssertionError()
        return attachment, message

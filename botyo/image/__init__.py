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
from argparse import ArgumentParser
from dataclasses import dataclass, asdict, field
from corestring import split_with_quotes


@dataclass
class ImageGeneratorParams:
    prompt: str
    height: int = field(default=512)
    width: int = field(default=512)
    guidance_scale: float = field(default=7.5)
    seed: Optional[int] = None


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


class ImageMeta(type):

    __image_generator_parser: Optional[ArgumentParser] = None

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

    def polygon(
        cls, attachment: Attachment, frequency: int = 800
    ) -> tuple[Attachment, dict]:
        return cls(attachment).do_polygon(frequency)

    @property
    def image_generator_parser(cls) -> ArgumentParser:
        if not cls.__image_generator_parser:
            parser = ArgumentParser(description='Image Processing', add_help=False)
            parser.add_argument('prompt', nargs='+')
            parser.add_argument('-h',
                                '--height', type=int, default=512)
            parser.add_argument('-w', '--width', type=int, default=512)
            parser.add_argument('-g', '--guidance_scale',
                                type=float, default=7)
            parser.add_argument('-s', '--seed', type=int)
            cls.__image_generator_parser = parser
        return cls.__image_generator_parser

    def image_generator_params(cls, prompt: str) -> ImageGeneratorParams:
        parser = cls.image_generator_parser
        parsed = parser.parse_args(split_with_quotes(prompt))
        return ImageGeneratorParams(
            prompt=" ".join(parsed.prompt),
            height=parsed.height,
            width=parsed.width,
            guidance_scale=parsed.guidance_scale,
            seed=parsed.seed
        )

    def variation(
        cls,
        attachment: Attachment,
        images: Optional[int] = None
    ) -> tuple[Attachment, dict]:
        return cls(attachment).do_variation(images)

    def txt2img(cls, prompt: str) -> tuple[Attachment, dict]:
        return cls().do_txt2img(prompt)

    def img2img(
        cls,
        attachment: Attachment,
        prompt: Optional[str] = None
    ) -> tuple[Attachment, dict]:
        return cls(attachment).do_img2img(prompt)


class Image(object, metaclass=ImageMeta):

    __attachment: Optional[Attachment] = None

    def __init__(self, attachment: Optional[Attachment] = None) -> None:
        self.__attachment = attachment

    def do_analyze(self):
        attachment, message = self.getResponse(Action.ANALYZE)
        if message:
            analyses = AnalyzeReponse.from_json(  # type: ignore
                message)
            rows = [
                ["Age: ", analyses.age],
                [
                    "Emotion: ",
                    analyses.dominant_emotion,
                    emojize(analyses.emotion_icon),
                ],
                ["Race: ", analyses.dominant_race,
                    emojize(analyses.race_icon)],
                ["Gender: ", analyses.gender, emojize(analyses.gender_icon)],
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

    def do_variation(self, images: Optional[int] = None):
        return self.getResponse(Action.VARIATION, images)

    def do_txt2anything(self, prompt: str):
        return self.getResponse(Action.TXT2IANYTHING, prompt)

    def do_txt2arcane(self, prompt: str):
        return self.getResponse(Action.TXT2ARCANE, prompt)

    def do_txt2disney(self, prompt: str):
        return self.getResponse(Action.TXT2DISNEY, prompt)

    def do_txt2img(self, prompt: str):
        params = __class__.image_generator_params(prompt)
        return self.getResponse(
            Action.TXT2IMG,
            params.prompt,
            json=asdict(params)
        )

    def do_img2img(self, prompt: Optional[str] = None):
        params = __class__.image_generator_params(prompt)
        return self.getResponse(
            Action.IMG2IMG,
            params.prompt,
            json=asdict(params)
        )

    def __make_request(self, path: str, json: Optional[dict] = None):
        attachment = self.__attachment
        params = {}

        if attachment:
            assert isinstance(attachment, dict)
            p = Path(attachment.get("path", ""))
            kind = filetype.guess(p.as_posix())
            mime = attachment.get("contentType")
            fp = p.open("rb")
            assert kind
            params['files'] = {"file": (f"{p.name}.{kind.extension}",
                                        fp, mime, {"Expires": "0"})}

        if json:
            params['data'] = json

        return Request(
            f"{Config.image.base_url}/{path}",
            method=Method.POST,
            **params
        )

    def getResponse(
        self,
        action: Action,
        action_param=None,
        json: Optional[dict] = None
    ):
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
                    b"content-type", b""  # type: ignore
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
            message = req.json
        return attachment, message

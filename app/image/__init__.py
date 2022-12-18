from pathlib import Path
from botyo_server.models import Attachment
from cachable.request import Request, Method
from cachable.storage.file import FileStorage
from app.core.config import Config
from uuid import uuid4
import filetype
from enum import Enum
from botyo_server.output import TextOutput
from emoji import emojize
from app.image.models import AnalyzeReponse


class Action(Enum):
    ANALYZE = "face/analyze"
    TAG = "face/tag"
    HOWCUTE = "face/howcute"
    CLASSIFY = "image/classify"
    PIXEL = "image/pixel"
    POLYGON = "image/polygon"
    VARIATION = "image/variation"


class ImageMeta(type):
    def __call__(cls, attachment: Attachment, *args, **kwds):
        return type.__call__(cls, attachment, *args, **kwds)

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

    def variation(cls, attachment: Attachment) -> tuple[Attachment, dict]:
        return cls(attachment).do_variation()


class Image(object, metaclass=ImageMeta):

    __attachment: Attachment

    def __init__(self, attachment: Attachment) -> None:
        self.__attachment = attachment

    def do_analyze(self):
        attachment, message = self.getResponse(Action.ANALYZE)
        if message:
            analyses: AnalyzeReponse = AnalyzeReponse.from_json(message)  # type: ignore
            rows = [
                ["Age: ", analyses.age],
                [
                    "Emotion: ",
                    analyses.dominant_emotion,
                    emojize(analyses.emotion_icon),
                ],
                ["Race: ", analyses.dominant_race, emojize(analyses.race_icon)],
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

    def do_variation(self):
        return self.getResponse(Action.VARIATION)

    def getResponse(self, action: Action, action_param=None):
        path = action.value
        if action_param:
            path = f"{path}/{action_param}"
        attachment = self.__attachment
        assert isinstance(attachment, dict)
        p = Path(attachment.get("path", ""))
        kind = filetype.guess(p.as_posix())
        mime = attachment.get("contentType")
        with p.open("rb") as fp:
            assert kind
            req = Request(
                f"{Config.image.base_url}/{path}",
                method=Method.POST,
                files={
                    "file": (f"{p.name}.{kind.extension}", fp, mime, {"Expires": "0"})
                },
            )
            message = ""
            is_multipart = req.is_multipart
            if is_multipart:
                multipart = req.multipart
                cp = FileStorage.storage_path
                for part in multipart.parts:
                    content_type = part.headers.get(
                        b"content-type", b""
                    ).decode()  # type: ignore
                    if "image/png" in content_type:
                        assert kind
                        fp = cp / f"{uuid4().hex}.{kind.extension}.png"
                        fp.write_bytes(part.content)
                        attachment = Attachment(
                            path=fp.absolute().as_posix(),
                            contentType="image/png",
                        )
                    elif "image/jpeg" in content_type:
                        assert kind
                        fp = cp / f"{uuid4().hex}.{kind.extension}.jpg"
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

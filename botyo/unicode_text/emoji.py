from pilmoji import Pilmoji
from PIL import Image, ImageFont
from pathlib import Path
from typing import Any, Optional
from corestring import string_hash
import base64
from io import BytesIO


class EmojiMeta(type):

    __instances: dict[str, 'Emoji'] = {}

    def __call__(cls, txt: str, *args: Any, **kwds: Any) -> Any:
        k = string_hash(txt)
        if k not in cls.__instances:
            cls.__instances[k] = type.__call__(cls, txt, *args, **kwds)
        return cls.__instances[k]

    @property
    def font(cls) -> ImageFont.FreeTypeFont:
        pth = Path(__file__).parent / 'NotoColorEmoji-Regular.ttf'
        return ImageFont.truetype(pth.as_posix(), 64)

    def b64(cls, txt: str) -> str:
        return cls(txt).base64


class Emoji(object, metaclass=EmojiMeta):

    __txt: str
    __image: Optional[Image.Image] = None
    __base64: Optional[str] = None

    def __init__(self, txt: str) -> None:
        self.__txt = txt

    @property
    def image(self) -> Image.Image:
        if not self.__image:
            with Image.new('RGBA', (64 * len(self.__txt), 64),
                           (255, 255, 255, 0)) as image:
                with Pilmoji(image) as pilmoji:
                    pilmoji.text((0, 0), self.__txt.strip(), (0, 0, 0),
                                 __class__.font)
                    self.__image = pilmoji.image
        return self.__image

    @property
    def base64(self) -> str:
        if not self.__base64:
            buffered = BytesIO()
            self.image.save(buffered, format="PNG")
            data = buffered.getvalue()
            self.__base64 = base64.b64encode(data).decode()  # type: ignore
        return f"data:image/png;base64,{self.__base64}"

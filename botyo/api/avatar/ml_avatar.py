from hashlib import blake2b
from pathlib import Path
from cachable.models import BinaryStruct
from cairosvg import svg2png
from multiavatar.multiavatar import multiavatar
from botyo.core.store import ImageCachable
from PIL import Image
from random import choice
import logging
from typing import Optional
from botyo.image import Image
from corestring import string_hash


from botyo.demographics import Demographics, Gender


class StableDiffusionAvatar(ImageCachable):

    _struct: Optional[BinaryStruct] = None
    _name: str
    __id = None
    __gender: Optional[Gender] = None
    SIZE = (512, 768)

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self._name = name

    def _init(self):
        if self.isCached:
            return
        try:
            attachment, _ = Image.txt2img(prompt=self.cmd)
            assert attachment
            ap = Path(attachment)
            ap.rename(self._path)
        except Exception:
            pass

    @property
    def gender(self) -> Gender:
        if not self.__gender:
            self.__gender = Demographics.gender(self._name)
        return self.__gender

    @property
    def cmd(self) -> str:
        return (
            f"portrait of {self._name}, {self.gender.value},highly detailed,"
            " digital painting, artstation, concept art, smooth, sharp focus, illustration, "
            "art by wlop, mars ravelo and greg rutkowski "
            "--width=512 --height=768 --guidance_scale=13"

        )

    @property
    def id(self):
        if not self.__id:
            self.__id = string_hash(self.cmd)
        return self.__id

    @property
    def filename(self):
        return f"{self.id}.png"

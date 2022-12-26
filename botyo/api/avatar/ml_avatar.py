from pathlib import Path
from cachable.models import BinaryStruct
from botyo.core.store import ImageCachable
from PIL import Image
import logging
from typing import Optional
from botyo.image import Image
from corestring import string_hash


from botyo.demographics import Demographics, Gender, Race


class StableDiffusionAvatar(ImageCachable):

    _struct: Optional[BinaryStruct] = None
    _name: str
    __id = None
    __gender: Optional[Gender] = None
    __race: Optional[Race] = None
    SIZE = (512, 512)

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
            ap = Path(attachment.path)
            ap.rename(self._path)
        except Exception:
            pass

    @property
    def gender(self) -> Gender:
        if not self.__gender:
            self.__gender = Demographics.gender(self._name)
        return self.__gender

    @property
    def race(self) -> Gender:
        if not self.__race:
            self.__race = Demographics.race(self._name)
        return self.__race

    @property
    def cmd(self) -> str:
        return (
            f"{self._name} portrait crazy {self.race.value} {self.gender.value} "
            " as the character by artgrem, centered, greg rutkowski, ross tran, kuvshinov"
            "--width=512 --height=512 --guidance_scale=12"
        )

    @property
    def id(self):
        if not self.__id:
            self.__id = string_hash(self.cmd)
        return self.__id

    @property
    def filename(self):
        return f"{self.id}.png"

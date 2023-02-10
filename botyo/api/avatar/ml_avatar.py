from pathlib import Path
from cachable.models import BinaryStruct
from botyo.core.store import ImageCachable
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
    __new: bool = False
    SIZE = (2048, 2048)

    def __init__(self, name: str, is_new: bool = False):
        if not name:
            raise ValueError
        self._name = name
        self.__new = is_new

    def _init(self):
        if self.isCached:
            return
        attachment, _ = Image.txt2img(prompt=self.cmd)
        assert attachment
        assert attachment.path
        assert self._path
        ap = Path(attachment.path)
        ap.rename(self._path)

    @property
    def isCached(self) -> bool:
        if self.__new:
            return False
        return super().isCached

    @property
    def gender(self) -> Gender:
        if not self.__gender:
            self.__gender = Demographics.gender(self._name)
        return self.__gender

    @property
    def race(self) -> Race:
        if not self.__race:
            self.__race = Demographics.race(self._name)
        return self.__race

    @property
    def cmd(self) -> str:
        object = [self._name]
        if not all([self._name.startswith("<"), self._name.endswith(">")]):
            object.append(self.gender.value)
            object.append(self.race.value)
        return (
            f"profile picture of  {' '.join(object)}, "
            "in the style of artgerm, gerald brom, atey ghailan and mike mignola, "
            "vibrant colors and hard shadows and strong rim light, plain background, "
            "comic cover art, trending on artstation -u"
        )

    @property
    def id(self):
        if not self.__id:
            self.__id = string_hash(self.cmd)
        return self.__id

    @property
    def filename(self):
        return f"{self.id}.png"

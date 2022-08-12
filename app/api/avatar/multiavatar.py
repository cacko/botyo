from hashlib import blake2b
from pathlib import Path
from traceback import print_exc
from cachable.models import BinaryStruct
from cairosvg import svg2png
from multiavatar.multiavatar import multiavatar
from cachable.cacheable import CachableFile
from PIL import Image
from py_avataaars import (
    PyAvataaar,
    AvatarEnum,
    AvatarStyle,
    AccessoriesType,
    FacialHairType,
    TopType,
)
from random import choice

from app.demographics import Demographics, Gender


class MultiAvatar(CachableFile):

    _struct: BinaryStruct = None
    _name = None
    __id = None
    SIZE = (200, 200)

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self._name = name

    def _init(self):
        if self.isCached:
            return
        try:
            avatar = multiavatar(self._name, None, None)
            svg2png(
                bytestring=avatar,
                write_to=self.storage_path.as_posix(),
                output_height=180,
                output_width=180,
            )
        except Exception:
            pass

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self._name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def filename(self):
        return f"{self.id}.png"


class Avataaar(MultiAvatar):

    _background: str = None

    def __init__(self, name: str, background: str):
        if not name:
            raise ValueError
        self._name = name
        self._background = background

    def _init(self):
        if self.isCached:
            return
        try:
            avatar = PyAvataaar()
            vrs = {k: choice(list(v.__class__))
                   for k, v in vars(avatar).items()
                   if isinstance(v, AvatarEnum)}
            gender = Demographics.gender(self._name)
            if gender == Gender.M:
                while vrs["top_type"].name.startswith("LONG"):
                    vrs["top_type"] = choice(list(TopType))
            else:
                vrs["facial_hair_type"] = FacialHairType.DEFAULT

            avatar = PyAvataaar(
                **{
                    **vrs,
                    "style": AvatarStyle.TRANSPARENT,
                    "accessories_type": AccessoriesType.DEFAULT,
                }
            )
            avatar.render_png_file(self.storage_path.as_posix())
            img = Image.open(self.storage_path.as_posix())
            img = img.convert('RGBA')
            img = img.resize(self.SIZE, Image.BICUBIC)
            BG = Path(__file__).parent / f"{self._background}.png"
            background = Image.open(BG.as_posix())
            background = background.resize(self.SIZE, Image.BICUBIC)
            background = background.convert('RGBA')
            background.paste(img, (10, 10), img)
            background.save(self.storage_path.as_posix(), "PNG")
        except Exception as e:
            print_exc(e)
            pass

    @property
    def filename(self):
        return f"{self.id}_{self._background}.png"

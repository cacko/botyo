import re
import tempfile
from dataclasses import dataclass
from enum import Enum
from hashlib import blake2b
from math import floor
from pathlib import Path
from typing import Any
from dataclasses_json import Undefined, dataclass_json
from emoji import demojize, emojize
from humanfriendly.tables import format_pretty_table, format_robust_table
from markdown import markdown
from PIL import Image, ImageDraw, ImageFont
from tabulate import tabulate
from texttable import Texttable
from textacy.preprocessing import pipeline, remove, replace
from .unicode_text import convert, STYLE_MONO


def clean_markdown(s: str):
    html = markdown(s)
    clean_pipeline = pipeline.make_pipeline(
        remove.accents,
        remove.brackets,
        remove.html_tags,
        replace.emojis,
        replace.hashtags,
    )
    return clean_pipeline(html)


def truncate(value: str, size=200, ellipsis="..."):
    value = value.strip()
    if not len(value) > size:
        return value
    limit = size - len(ellipsis)
    cut = value[:limit]
    return f"{cut}{ellipsis}"


class Align(Enum):
    LEFT = "<"
    RIGHT = ">"
    CENTER = "^"


def shorten(text: str, size: int, placeholder: str = "..", extraSize=0):
    if not isinstance(text, str):
        return text
    size += max([0, extraSize])
    if len(text) <= size:
        return text.strip()
    return f"{text.strip()[:size-len(placeholder)].strip()}{placeholder}"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Column:
    size: int = 27
    align: Align = Align.LEFT
    title: str = " "
    spacing: int = 0
    fullsize: bool = False

    def cell(self, val):
        if self.fullsize:
            return val
        return f"{shorten(val, self.size):{self.align.value}{self.size}}"

    @property
    def header(self):
        return f"{shorten(self.title, self.size):{self.align.value}{self.size}}"

    @property
    def leading(self):
        return f"{shorten(self.title, floor(self.size/4)):{self.align.value}{floor(self.size/4)}}"


WHITESPACE = 8199
NEWLINE = [10, 13]
NOTCOMPATIBLE = ""


class OutputMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(OutputMeta,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def addColumns(cls,
                   cols: list[Column],
                   content: list[list[str]],
                   with_header=False):
        return cls().add_columns(cols, content, with_header)

    def clean(cls):
        cls().clean_items()

    def addRows(cls, rows: list[Any]):
        return cls().add_rows(rows)

    def image(cls, text) -> Path:
        return cls().to_image(text)

    def toMono(cls, text):
        return cls().to_mono(text)

    def alignWhitespace(cls, text):
        return cls().align_whitespace(text)

    def splitWithQuotes(cls, text):
        return cls().split_with_quotes(text)

    def addTable(cls, cols, rows):
        return cls().get_table(cols, rows)

    def addRobustTable(cls, cols, rows):
        return cls().get_robust_table(cols, rows)

    def addPrestoTable(cls, cols, rows):
        return cls().get_presto_table(cols, rows)

    def addDecoTable(cls, cols, rows):
        return cls().get_deco_table(cols, rows)

    def render(cls, joiner="\n"):
        return cls().get_content(joiner)

    @property
    def utf8mono(cls):
        return cls().utf8Mono

    @utf8mono.setter
    def utf8mono(cls, val: bool):
        cls().utf8mono = val


class Output(object, metaclass=OutputMeta):

    utf8mono = False
    items: list[str] = []

    def clean_items(self):
        self.items = []

    def to_image(self, text: str) -> Path:
        id = blake2b(digest_size=20)
        id.update(text.encode())
        output_filename = Path(tempfile.gettempdir()) / f"{id.hexdigest()}.png"
        im = Image.new("RGBA", (1000, 800), (45, 108, 234, 255))
        draw = ImageDraw.Draw(im)
        try:
            monoFont = ImageFont.truetype(font="./SourceCodePro-Medium.ttf",
                                          size=35)
            draw.text((50, 10), text, fill="white", font=monoFont)
        except Exception:
            draw.text((10, 10), text, fill="white")
        im.save(output_filename)
        return output_filename

    def add_columns(self,
                    columns: tuple[Column],
                    content: tuple[str],
                    with_header=False):
        rows = [
            "".join([
                self.to_mono(col.cell(cell))
                for col, cell in zip(columns, cnt)
            ]) for cnt in content
        ]
        if with_header:
            cols = "".join([self.to_mono(col.header) for col in columns])
            self.items = [
                *self.items,
                self.align_whitespace(cols),
                *map(self.align_whitespace, rows),
            ]
        else:
            self.items = [*self.items, *map(self.align_whitespace, rows)]

    def add_rows(self, rows: list[Any]):
        self.items = [
            *self.items,
            *map(lambda x: self.align_whitespace(self.to_mono(str(x))), rows),
        ]

    def get_table(self, columns: tuple[Column], content: tuple[str]):
        rows = [[
            self.to_mono(col.cell(cell)) for col, cell in zip(columns, cnt)
        ] for cnt in content]
        cols = [self.to_mono(col.header) for col in columns]

        table = format_pretty_table(rows, cols)

        self.items = [*self.items, table]

    def get_robust_table(self, columns: tuple[Column], content: tuple[str]):
        rows = [[
            self.to_mono(col.cell(cell)) for col, cell in zip(columns, cnt)
        ] for cnt in content]
        cols = [self.to_mono(col.leading) for col in columns]

        table = format_robust_table(rows, cols)

        self.items = [*self.items, table]

    def get_presto_table(self, columns: tuple[Column], content: tuple[str]):
        cols = [self.to_mono(col.leading) for col in columns]
        rows = [[
            self.to_mono(col.cell(cell)) for col, cell in zip(columns, cnt)
        ] for cnt in content]
        table = tabulate(rows, headers=cols, tablefmt="presto")
        self.items = [*self.items, table]

    def get_deco_table(self, columns: tuple[Column], content: tuple[str]):
        cols = [col.title for col in columns]
        rows = [[cell for _, cell in zip(columns, cnt)] for cnt in content]
        table = Texttable()
        table.set_cols_width([col.size for col in columns])
        table.add_rows([cols, *rows])
        self.items = [*self.items, str(table.draw()) + "\n"]

    def get_content(self, joiner="\n"):
        result = joiner.join(self.items)
        self.items = []
        return result

    def align_whitespace(self, text: str):
        if not self.utf8mono:
            return text
        return re.sub(r"\s", chr(WHITESPACE), text)

    def to_mono(self, text: str):
        text = emojize(demojize(f"{text}"))
        if not self.utf8mono:
            return text
        return convert(text, STYLE_MONO)

    def split_with_quotes(self, text: str) -> list[str]:
        return [
            x.strip() for x in filter(lambda x: len(x.strip()) > 0,
                                      text.split('"' if '"' in text else " "))
        ]


class ImageOutput(Output):
    utf8mono = False


class TextOutput(Output):
    utf8mono = False


def to_mono(text):
    return TextOutput.toMono(text)


def align_whitespace(text):
    return TextOutput.alignWhitespace(text)


def split_with_quotes(text):
    return TextOutput.splitWithQuotes(text)

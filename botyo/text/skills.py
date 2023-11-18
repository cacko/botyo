import logging
from typing import Any
from pydantic import BaseModel
from enum import StrEnum
from botyo.server.output import TextOutput, Column
from itertools import groupby


class EntityGroup(StrEnum):
    TECHNICAL = "TECHNICAL"
    BUS = "BUS"
    TECHNOLOGY = "TECHNOLOGY"
    SOFT = "SOFT"


class Token(BaseModel):
    entity_group: EntityGroup
    score: float
    word: str


def output(response: list[Any]):
    tokens = [Token(**t) for t in response]
    tokens = sorted(tokens, key=lambda t: t.entity_group)
    cols = []
    row = []
    for col, data in groupby(tokens, key=lambda t: t.entity_group):
        cols.append(Column(title=col, size=12))
        row.append(", ".join(set([t.word.capitalize() for t in data])))
    logging.warning(cols)
    logging.warning(row)
    TextOutput.addRobustTable(cols, [row])
    return TextOutput.render()

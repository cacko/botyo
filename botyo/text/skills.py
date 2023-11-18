from typing import Any
from pydantic import BaseModel
from enum import StrEnum
from botyo.server.output import TextOutput
from itertools import groupby
from emoji import emojize


class EntityIcon(StrEnum):
    TECHNICAL = ":desktop_computer"
    BUS = ":department_store:"
    TECHNOLOGY = ":wrench:"
    SOFT = ":man_office_worker:"


class EntityGroup(StrEnum):
    TECHNICAL = "TECHNICAL"
    BUS = "BUS"
    TECHNOLOGY = "TECHNOLOGY"
    SOFT = "SOFT"

    @property
    def icon(self) -> EntityIcon:
        return EntityIcon[self.name]

    @property
    def title(self) -> str:
        return emojize(f"{self.icon.value} {self.value.capitalize()}")


class Token(BaseModel):
    entity_group: EntityGroup
    score: float
    word: str


def output(response: list[Any]):
    tokens = [Token(**t) for t in response]
    tokens = sorted(tokens, key=lambda t: t.entity_group)
    for col, data in groupby(tokens, key=lambda t: t.entity_group):
        row = [f"{EntityGroup(col).title:<14}:"]
        row.append(", ".join(set([t.word.capitalize() for t in data])))
        TextOutput.add_rows(rows=[" ".join(row)])
    return TextOutput.render()

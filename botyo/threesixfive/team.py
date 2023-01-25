from stringcase import snakecase
from pathlib import Path
from enum import Enum
import re
from functools import reduce

DEFAULT_BADGE = Path(__file__).parent / "default.png"

TEAM_NORMALISERS = {
    r"atl\.": "Atletico",
    r"paris sg": "PSG",
    r"nottm": "Nottingham",
    r"sheff": "Sheffield",
    r"utd\.*": "United"
}


class AssetKey(Enum):
    TEAM_BADGE = "team_"
    LIVESCORE_DETAILS = "livescore_details_"


def store_key(obj: AssetKey, id: str) -> str:
    if obj == AssetKey.TEAM_BADGE:
        return f"{AssetKey.TEAM_BADGE.value}{snakecase(id)}"
    elif obj == AssetKey.LIVESCORE_DETAILS:
        return f"{AssetKey.LIVESCORE_DETAILS.value}{snakecase(id)}"
    else:
        raise NotImplementedError


def normalize_team(team: str):
    return reduce(
        lambda r, k: re.compile(k, re.IGNORECASE).sub(TEAM_NORMALISERS.get(k), r),
        TEAM_NORMALISERS.keys(),
        team,
    )

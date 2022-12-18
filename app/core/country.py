from pycountry import countries
import flag
from dataclasses import dataclass
from typing import Optional


@dataclass
class Country:
    name: str

    @property
    def flag(self):
        try:
            matches = countries.search_fuzzy(self.name)
            return flag.flagize(f":{matches.pop(0).alpha_2}:", subregions=False)
        except LookupError:
            return ""

    def with_flag(self, name: Optional[str] = None) -> str:
        if not name:
            name = self.name
        try:
            matches = countries.search_fuzzy(self.name)
            return flag.flagize(
                f":{matches.pop(0).alpha_2}:{name}", subregions=False
            )
        except LookupError:
            return name

from pycountry import countries
import flag
from dataclasses import dataclass


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

    @property
    def country_with_flag(self) -> str:
        try:
            matches = countries.search_fuzzy(self.name)
            return flag.flagize(
                f":{matches.pop(0).alpha_2}:{self.name}", subregions=False
            )
        except LookupError:
            return self.name

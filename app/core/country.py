from pycountry import countries
import flag
from dataclasses import dataclass

@dataclass
class Country:
    name: str

    @property
    def flag(self):
        if not self.name:
            return ""
        matches = countries.search_fuzzy(self.name)
        if not len(matches):
            return ""
        return flag.flagize(f":{matches.pop(0).alpha_2}:", subregions=False)

    @property
    def country_with_flag(self) -> str:
        if not self.name:
            return ""
        matches = countries.search_fuzzy(self.name)
        if not len(matches):
            return self.name
        return flag.flagize(f"{self.name} :{matches.pop(0).alpha_2}:", subregions=False)

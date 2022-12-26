from dataclasses import dataclass
from dataclasses_json import dataclass_json
from enum import Enum
from fuzzelinho import Match, MatchMethod
from botyo.core.config import Config
from botyo.server.output import split_with_quotes
from botyo.chatyo import getResponse, Payload


class Gender(Enum):
    M = "male"
    F = "female"
    G = "faggot"
    U = "unknown"


class Race(Enum):
    BRITISH = "GreaterEuropean,British"
    FRENCH = "GreaterEuropean,WestEuropean,French"
    ITALIAN = "GreaterEuropean,WestEuropean,Italian"
    HISPANIC = "GreaterEuropean,WestEuropean,Hispanic"
    JEWISH = "GreaterEuropean,Jewish"
    EASTEURO = "GreaterEuropean,EastEuropean"
    INDOPAK = "Asian,IndianSubContinent"
    JAPANESE = "Asian,GreaterEastAsian,Japanese"
    MUSLIM = "GreaterAfrican,Muslim"
    ASIAN = "Asian,GreaterEastAsian,EastAsian"
    NORDIC = "GreaterEuropean,WestEuropean,Nordic"
    GERMAN = "GreaterEuropean,WestEuropean,Germanic"
    AFRICAN = "GreaterAfrican,Africans"
    FAGGOT = "Faggot"


class NameMatch(Match):
    minRatio = 80
    method = MatchMethod.PARTIALSET


@dataclass_json
@dataclass
class NameNeedle:
    name: str


class DemographicsMeta(type):

    _instance = None
    _app = None
    _genderClassifier = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def register(cls, app):
        cls._instance = cls()

    def gender(cls, name: str) -> Gender:
        if cls.isFaggot(name=name):
            return Gender.F
        if cls.isMale(name):
            return Gender.M
        result = cls().getGender(split_with_quotes(name)[0])
        return result

    def race(cls, name: str) -> Race:
        result = cls().getRace(name)
        return result

    def isMale(cls, name: str) -> bool:
        matcher = NameMatch([
            NameNeedle(name=male)
            for male in Config.demographics.males
        ])
        return len(matcher.fuzzy(NameNeedle(name=name))) > 0

    def isFaggot(cls, name: str) -> bool:
        matcher = NameMatch([
            NameNeedle(name=fag)
            for fag in Config.demographics.faggots
        ])
        return len(matcher.fuzzy(NameNeedle(name=name))) > 0


class Demographics(object, metaclass=DemographicsMeta):

    def getRace(self, name: str) -> Race:
        res = getResponse(
            "name/race",
            Payload(message=name)
        )
        return Race(res.response)

    def getGender(self, name: str) -> Gender:
        res = getResponse("name/gender", Payload(message=name))
        return Gender(res.response)

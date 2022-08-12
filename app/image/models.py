from dataclasses_json import dataclass_json, Undefined, config
from dataclasses import dataclass, field
from enum import Enum
from stringcase import constcase


class EmotionIcon(Enum):
    ANGRY = ":angry_face:"
    DISGUST = ":face_vomiting:"
    FEAR = ":face_screaming_in_fear:"
    HAPPY = ":grinning_face_with_big_eyes:"
    NEUTRAL = ":neutral_face:"
    SAD = ":disappointed_face:"
    SURPRISE = ":astonished_face:"


class RaceIcon(Enum):
    ASIAN_MAN = ":globe_showing_Asia-Australia:"
    ASIAN_WOMAN = ":globe_showing_Asia-Australia:"
    BLACK_MAN = ":man_cook_dark_skin_tone:"
    BLACK_WOMAN = ":woman_dark_skin_tone:"
    INDIAN_MAN = ":man_medium-dark_skin_tone_beard:"
    INDIAN_WOMAN = ":man_medium-dark_skin_tone_beard:"
    LATINO_HISPANIC_MAN = ":Spain:"
    LATINO_HISPANIC_WOMAN = ":Spain:"
    MIDDLE_EASTERN_MAN = ":star_and_crescent:"
    MIDDLE_EASTERN_WOMAN = ":star_and_crescent:"
    WHITE_MAN = ":man_light_skin_tone_beard:"
    WHITE_WOMAN = ":woman_medium-light_skin_tone_white_hair:"


class GenderIcon(Enum):
    MAN = ":male_sign:"
    WOMAN = ":female_sign:"
    FAGGOT = ":middle_finger:"
    UNKNOWN = ":alien:"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EmotionScores:
    angry: float
    disgust: float
    fear: float
    happy: float
    neutral: float
    sad: float
    surprise: float

    @property
    def emotion(self):
        pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RaceScores:
    asian: float
    black: float
    indian: float
    latino_hispanic: float = field(
        metadata=config(field_name="latino hispanic"))
    middle_eastern: float = field(metadata=config(field_name="middle eastern"))
    white: float

    @property
    def race(self):
        pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FaceRegion:
    h: int
    w: int
    x: int
    y: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AnalyzeReponse:
    age: int
    dominant_emotion: str
    dominant_race: str
    emotion: EmotionScores
    gender: str
    race: RaceScores
    region: FaceRegion

    @property
    def emotion_icon(self) -> str:
        return EmotionIcon[constcase(self.dominant_emotion)].value

    @property
    def race_icon(self) -> str:
        parts = map(constcase, [self.dominant_race, self.gender])
        return RaceIcon['_'.join(parts)].value

    @property
    def gender_icon(self) -> str:
        return GenderIcon[constcase(self.gender)].value

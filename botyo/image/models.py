from enum import StrEnum
from stringcase import constcase
from pydantic import BaseModel, Field


class Choices(object):

    @classmethod
    def values(cls):
        return [m.value for m in cls.__members__.values()]

    @classmethod
    def keys(cls):
        return [m.lower() for m in cls.__members__.keys()]


class EmotionIcon(StrEnum):
    ANGRY = ":angry_face:"
    DISGUST = ":face_vomiting:"
    FEAR = ":face_screaming_in_fear:"
    HAPPY = ":grinning_face_with_big_eyes:"
    NEUTRAL = ":neutral_face:"
    SAD = ":disappointed_face:"
    SURPRISE = ":astonished_face:"


class RaceIcon(StrEnum):
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


class GenderIcon(StrEnum):
    MAN = ":male_sign:"
    WOMAN = ":female_sign:"
    FAGGOT = ":middle_finger:"
    UNKNOWN = ":alien:"


class BotyoPrompt(StrEnum):
    MAGICGLOW = ("[placeholder] skill magic deepdream radiating a "
                 "glowing aura stuff loot legends stylized digital "
                 "illustration video game icon artstation lois van "
                 "baarle, ilya kuvshinov, rossdraws ")


class EmotionScores(BaseModel):
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


class RaceScores(BaseModel):
    asian: float
    black: float
    indian: float
    latino_hispanic: float = Field(alias="latino hispanic")
    middle_eastern: float = Field(alias="middle eastern")
    white: float

    @property
    def race(self):
        pass


class FaceRegion(BaseModel):
    h: int
    w: int
    x: int
    y: int


class AnalyzeReponse(BaseModel):
    age: int
    dominant_emotion: str
    dominant_race: str
    dominant_gender: str
    region: FaceRegion

    @property
    def emotion_icon(self) -> str:
        return EmotionIcon[constcase(self.dominant_emotion)].value

    @property
    def race_icon(self) -> str:
        parts = map(constcase, [self.dominant_race, self.dominant_gender])
        return RaceIcon["_".join(parts)].value

    @property
    def gender_icon(self) -> str:
        return GenderIcon[constcase(self.dominant_gender)].value


class Upload2Wallies(BaseModel):
    image_url: str
    category: str
    upscale: bool = Field(default=True)


class KonkatFile(BaseModel):
    collage_id: str
    filename: str
    url: str

from enum import Enum
from stringcase import titlecase
from botyo_server.blueprint import Blueprint
from botyo_server.output import TextOutput
from botyo_server.socket.connection import Context
from app.api import ZMethod
from botyo_server.models import RenderResult, EmptyResult
from app.demographics import Demographics, Gender, Race


bp = Blueprint("name")


class GenderIcon(Enum):
    M = ":male_sign:"
    F = ":female_sign:"
    G = ":middle_finger:"
    U = ":alien:"


class RaceIcon(Enum):
    BRITISH = ":United_Kingdom:"
    FRENCH = ":France:"
    ITALIAN = ":Italy:"
    HISPANIC = ":Spain:"
    JEWISH = ":Israel:"
    EASTEURO = ":European_Union:"
    INDOPAK = ":India:"
    JAPANESE = ":Japan:"
    MUSLIM = ":star_and_crescent:"
    ASIAN = "A:globe_showing_Asia-Australia:"
    NORDIC = ":polar_bear:"
    GERMAN = ":Germany:"
    AFRICAN = ":gorilla:"
    FAGGOT = ":middle_finger:"


@bp.command(
    method=ZMethod.NAME_GENDER,
    desc="genderiya"
)
def gender_command(context: Context):
    name = context.query

    if not name:
        return EmptyResult(method=ZMethod.NAME_GENDER)

    gender = None
    if Demographics.isFaggot(name):
        gender = Gender.G
    else:
        gender = Demographics.gender(name)

    if not gender:
        return EmptyResult(method=ZMethod.NAME_GENDER)

    icon = getattr(GenderIcon, gender.name)
    TextOutput.addRows(
        [f"{name.upper()} {icon.value} {titlecase(gender.value)}"])
    res = RenderResult(
        method=ZMethod.NAME_GENDER,
        message=TextOutput.render()
    )
    return res


@bp.command(
    method=ZMethod.NAME_RACE,
    desc="Batko's Life Matters"
)
def race_command(context: Context):
    name = context.query

    if not name:
        return EmptyResult(method=ZMethod.NAME_GENDER)

    race = None
    if Demographics.isFaggot(name):
        race = Race.FAGGOT
    else:
        race = Demographics.race(name)

    if not race:
        return EmptyResult(method=ZMethod.NAME_RACE)

    icon = getattr(RaceIcon, race.name)
    TextOutput.addRows(
        [f"{name.upper()} {icon.value} {titlecase(race.value)}"])
    res = RenderResult(
        method=ZMethod.NAME_RACE,
        message=TextOutput.render()
    )
    return res

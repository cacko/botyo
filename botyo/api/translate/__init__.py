from botyo.server.models import RenderResult
from botyo.server.socket.connection import Context
from botyo.server.blueprint import Blueprint
from botyo.chatyo import getResponse, Payload
from flag import flag
from botyo.server.models import ZMethod

bp = Blueprint("translate")


def translate_cmd(method: ZMethod, context: Context, flag_code: str):
    msg = context.query
    if not msg:
        return None
    json = getResponse(
        "/".join(method.value.split(":")), Payload(message=msg, source=context.source)
    )
    res = RenderResult(
        message=f"{flag(flag_code)} {json.response}", method=method, plain=True
    )
    return res


@bp.command(method=ZMethod.TRANSLATE_EN_ES, desc="en -> es", icon="")  # type: ignore
def enes_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_ES, context, "ES")


@bp.command(method=ZMethod.TRANSLATE_ES_EN, desc="es -> be")  # type: ignore
def esen_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_ES_EN, context, ":gb-eng:")


@bp.command(method=ZMethod.TRANSLATE_EN_BG, desc="en -> bg")  # type: ignore
def enbg_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_BG, context, "BG")


@bp.command(method=ZMethod.TRANSLATE_BG_EN, desc="bg -> en")  # type: ignore
def bgen_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_BG_EN, context, ":gb-eng:")


@bp.command(method=ZMethod.TRANSLATE_EN_CS, desc="en -> cs")  # type: ignore
def encs_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_CS, context, "CZ")


@bp.command(method=ZMethod.TRANSLATE_CS_EN, desc="cs -> en")  # type: ignore
def csen_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_CS_EN, context, ":gb-eng:")



@bp.command(method=ZMethod.TRANSLATE_EN_PL, desc="en -> pl")  # type: ignore
def enpl_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_PL, context, "PL")


@bp.command(method=ZMethod.TRANSLATE_PL_EN, desc="pl -> en")  # type: ignore
def plen_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_PL_EN, context, ":gb-eng:")


@bp.command(method=ZMethod.TRANSLATE_EN_FR, desc="en -> fr")  # type: ignore
def enfr_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_FR, context, "FR")


@bp.command(method=ZMethod.TRANSLATE_FR_EN, desc="fr -> en")  # type: ignore
def fren_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_FR_EN, context, ":gb-eng:")


@bp.command(method=ZMethod.TRANSLATE_EN_IT, desc="en -> it")  # type: ignore
def enit_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_EN_IT, context, "IT")


@bp.command(method=ZMethod.TRANSLATE_IT_EN, desc="it -> en")  # type: ignore
def iten_command(context: Context):
    return translate_cmd(ZMethod.TRANSLATE_IT_EN, context, ":gb-eng:")


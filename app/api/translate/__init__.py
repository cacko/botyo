from botyo_server.models import RenderResult
from botyo_server.socket.connection import Context
from botyo_server.blueprint import Blueprint
from app.chatyo import getResponse, Payload
from flag import flag
from app.api import ZMethod

bp = Blueprint("translate")


def translate_cmd(
    method: ZMethod,
    context: Context,
    flag_code: str
):
    msg = context.query
    if not msg:
        return None
    json = getResponse(
        "/".join(method.value.split(":")),
        Payload(
            message=msg,
            source=context.source
        )
    )
    res = RenderResult(
        message=f"{flag(flag_code)} {json.response}",
        method=method,
        plain=True
    )
    return res


@bp.command(
    method=ZMethod.TRANSLATE_EN_ES,
    desc="en -> es"
)
def enes_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_EN_ES,
        context,
        'ES'
    )


@bp.command(
    method=ZMethod.TRANSLATE_ES_EN,
    desc="es -> be"
)
def esen_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_ES_EN,
        context,
        ':gb-eng:'
    )


@bp.command(
    method=ZMethod.TRANSLATE_EN_BG,
    desc="en -> bg"
)
def enbg_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_EN_BG,
        context,
        'BG'
    )


@bp.command(
    method=ZMethod.TRANSLATE_BG_EN,
    desc="bg -> en"
)
def bgen_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_BG_EN,
        context,
        ':gb-eng:'
    )


@bp.command(
    method=ZMethod.TRANSLATE_EN_CS,
    desc="bg -> en"
)
def encs_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_EN_CS,
        context,
        'CZ'
    )


@bp.command(
    method=ZMethod.TRANSLATE_CS_EN,
    desc="bg -> en"
)
def csen_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_CS_EN,
        context,
        ':gb-eng:'
    )


@bp.command(
    method=ZMethod.TRANSLATE_PL_EN,
    desc="bg -> en"
)
def plen_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_PL_EN,
        context,
        ':gb-eng:'
    )


@bp.command(
    method=ZMethod.TRANSLATE_EN_PL,
    desc="bg -> en"
)
def enpl_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_EN_PL,
        context,
        'PL'
    )


@bp.command(
    method=ZMethod.TRANSLATE_SQ_EN,
    desc="sq -> en"
)
def sqen_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_SQ_EN,
        context,
        ':gb-eng:'
    )


@bp.command(
    method=ZMethod.TRANSLATE_EN_SQ,
    desc="en -> sq"
)
def ensq_command(context: Context):
    return translate_cmd(
        ZMethod.TRANSLATE_EN_SQ,
        context,
        'AL'
    )

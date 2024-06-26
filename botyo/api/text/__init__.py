from emoji import emojize
from botyo.server.models import ZMethod
from botyo.server.models import RenderResult
from botyo.server.socket.connection import Context
from botyo.server.blueprint import Blueprint
from botyo.chatyo import getResponse, Payload
from botyo.text.skills import output as skills_output

bp = Blueprint("text")


@bp.command(
    method=ZMethod.TEXT_GENERATE,
    desc="continue the sentence",
    icon="create"
)  # type: ignore
def dialog_commang(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/generate", Payload(message=msg, source=context.source))
    res = RenderResult(message=json.response, method=ZMethod.TEXT_GENERATE)
    return res


@bp.command(
    method=ZMethod.TEXT_DETECT,
    desc="find the tongue",
    icon="translate"
)  # type: ignore
def detect_commmand(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/detect", Payload(message=msg, source=context.source))
    res = RenderResult(
        message=f"{emojize(':loudspeaker:')} {json.response}",
        method=ZMethod.TEXT_DETECT,
    )
    return res


@bp.command(
    method=ZMethod.TEXT_SKILLS,
    desc="extract skills from job description",
    icon="rowing"
)  # type: ignore
def skills_commmand(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/skills", Payload(message=msg, source=context.source))
    res = RenderResult(
        message=skills_output(json.response),
        method=ZMethod.TEXT_SKILLS,
    )
    return res

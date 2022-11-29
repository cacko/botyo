from emoji import emojize
from app.api import ZMethod
from botyo_server.models import RenderResult
from botyo_server.socket.connection import Context
from botyo_server.blueprint import Blueprint
from app.chatyo import getResponse, Payload

bp = Blueprint("text")


@bp.command(method=ZMethod.TEXT_GENERATE, desc="continue the sentence")  # type: ignore
def dialog_commang(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/generate", Payload(message=msg, source=context.source))
    res = RenderResult(message=json.response, method=ZMethod.TEXT_GENERATE)
    return res


@bp.command(method=ZMethod.TEXT_DETECT, desc="find the tongue")  # type: ignore
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

from emoji import emojize
from botyo.api import ZMethod
from botyo.server.models import RenderResult
from botyo.server.socket.connection import Context
from botyo.server.blueprint import Blueprint
from botyo.chatyo import getResponse, Payload
import logging

bp = Blueprint("text")


@bp.command(method=ZMethod.TEXT_GENERATE, desc="continue the sentence")  # type: ignore
def dialog_commang(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/generate", Payload(message=msg, source=context.source))
    logging.warning(f">>TEXT_GENERATE {json}")
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

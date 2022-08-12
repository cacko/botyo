from app.chat import Chat
from botyo_server.blueprint import Blueprint
from botyo_server.socket.connection import Context
from botyo_server.models import RenderResult, ZSONMatcher
from app.api import ZMethod


bp = Blueprint("chat")


@bp.command(
    method=ZMethod.CHAT_DIALOG,
    matcher=ZSONMatcher.SOURCE
)
def dialog_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.dialog(source=context.source, text=msg, lang=context.lang)
    res = RenderResult(
        message=resp.response,
        method=ZMethod.CHAT_DIALOG,
        plain=True
    )
    return res


@bp.command(
    method=ZMethod.CHAT_PHRASE,
    matcher=ZSONMatcher.PHRASE,
    response="you coming today",
)
def phrase_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.phrase(msg)
    res = RenderResult(
        message=resp.response,
        method=ZMethod.CHAT_PHRASE,
        plain=True
    )
    return res

@bp.command(
    method=ZMethod.CHAT_REPLY,
    desc="genereate reply"
)
def reply_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.phrase(msg)
    res = RenderResult(
        message=resp.response,
        method=ZMethod.CHAT_PHRASE,
        plain=True
    )
    return res

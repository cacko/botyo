from botyo.chat import Chat
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import RenderResult, ZSONMatcher
from botyo.server.models import ZMethod


bp = Blueprint("chat")


@bp.command(
    method=ZMethod.CHAT_DIALOG,
    matcher=ZSONMatcher.SOURCE,
    subscription=True,
    icon="chat"
)  # type: ignore
def dialog_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.dialog(source=context.source, text=msg, lang=context.lang)
    res = RenderResult(message=resp.response, method=ZMethod.CHAT_DIALOG, plain=True)
    return res


@bp.command(
    method=ZMethod.CHAT_YOUCOMINGTODAY,
    matcher=ZSONMatcher.PHRASE,
    response="you coming today",
    subscription=True
)  # type: ignore
def phrase_you_coming_today(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.phrase(msg)
    res = RenderResult(message=resp.response,
                       method=ZMethod.CHAT_YOUCOMINGTODAY, plain=True)
    return res


@bp.command(
    method=ZMethod.CHAT_MINDBLOWINGINNIT,
    matcher=ZSONMatcher.PHRASE,
    response="mind blowing innit",
    subscription=True
)  # type: ignore
def phrase_mind_blowing(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Chat.phrase(msg)
    res = RenderResult(message=resp.response,
                       method=ZMethod.CHAT_MINDBLOWINGINNIT, plain=True)
    return res

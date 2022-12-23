from botyo.api.avatar.multiavatar import Avataaar, MultiAvatar
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, EmptyResult, RenderResult
from botyo.server.models import ZMethod
from botyo.server.blueprint import Blueprint

bp = Blueprint("avatar")


@bp.command(method=ZMethod.AVATAR_AVATAR, desc="generates avatar for the input")  # type: ignore
def avatar_command(context: Context) -> RenderResult:
    avatar = MultiAvatar(context.query)
    path = avatar.path
    res = (
        RenderResult(
            method=ZMethod.AVATAR_AVATAR,
            attachment=Attachment(path=path.as_posix(), contentType=avatar.contentType),
        )
        if path
        else EmptyResult()
    )
    return res


@bp.command(method=ZMethod.AVATAR_RUSSIA, desc="generates avatar for the input")  # type: ignore
def avaru_command(context: Context) -> RenderResult:
    avatar = Avataaar(context.query, "ru")
    path = avatar.path
    res = (
        RenderResult(
            method=ZMethod.AVATAR_RUSSIA,
            attachment=Attachment(path=path.as_posix(), contentType=avatar.contentType),
        )
        if path
        else EmptyResult()
    )
    return res


@bp.command(method=ZMethod.AVATAR_UKRAINE, desc="generates avatar for the input")  # type: ignore
def avauk_command(context: Context) -> RenderResult:
    avatar = Avataaar(context.query, "uk")
    path = avatar.path
    res = (
        RenderResult(
            method=ZMethod.AVATAR_UKRAINE,
            attachment=Attachment(path=path.as_posix(), contentType=avatar.contentType),
        )
        if path
        else EmptyResult()
    )
    return res

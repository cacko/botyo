from botyo.api.avatar.multiavatar import Avataaar, MultiAvatar
from botyo.api.avatar.ml_avatar import StableDiffusionAvatar
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, EmptyResult, RenderResult
from botyo.server.models import ZMethod
from botyo.server.blueprint import Blueprint
from argparse import ArgumentParser

bp = Blueprint("avatar")

parser = ArgumentParser(description="Avatar arguments")
parser.add_argument('prompt', nargs='+')
parser.add_argument('-n', '--new', action='store_true')
# type: ignore
@bp.command(method=ZMethod.AVATAR_AVATAR, desc="generates avatar for the input")
def avatar_command(context: Context) -> RenderResult:
    try:
        avatar = StableDiffusionAvatar(context.query)
        path = avatar.path
        assert path.exists()
        return RenderResult(
            method=ZMethod.AVATAR_AVATAR,
            attachment=Attachment(
                path=path.as_posix(),
                contentType=avatar.contentType
            ),
        )
    except AssertionError:
        return EmptyResult()


# type: ignore
@bp.command(method=ZMethod.AVATAR_RUSSIA, desc="generates avatar for the input")
def avaru_command(context: Context) -> RenderResult:
    avatar = Avataaar(context.query, "ru")
    path = avatar.path
    res = (
        RenderResult(
            method=ZMethod.AVATAR_RUSSIA,
            attachment=Attachment(path=path.as_posix(),
                                  contentType=avatar.contentType),
        )
        if path
        else EmptyResult()
    )
    return res


# type: ignore
@bp.command(method=ZMethod.AVATAR_UKRAINE, desc="generates avatar for the input")
def avauk_command(context: Context) -> RenderResult:
    avatar = Avataaar(context.query, "uk")
    path = avatar.path
    res = (
        RenderResult(
            method=ZMethod.AVATAR_UKRAINE,
            attachment=Attachment(path=path.as_posix(),
                                  contentType=avatar.contentType),
        )
        if path
        else EmptyResult()
    )
    return res

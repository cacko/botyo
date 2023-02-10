from botyo.api.avatar.ml_avatar import StableDiffusionAvatar
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, EmptyResult, RenderResult
from botyo.server.models import ZMethod
from botyo.server.blueprint import Blueprint
from argparse import ArgumentParser, ArgumentError
from corestring import split_with_quotes
import logging

bp = Blueprint("avatar")


# type: ignore


@bp.command(
    method=ZMethod.AVATAR_AVATAR, desc="generates avatar for the input", icon="face"
)  # type: ignore
def avatar_command(context: Context) -> RenderResult:
    try:
        assert context.query
        parser = ArgumentParser(description="Avatar arguments",
                                add_help=False, exit_on_error=False)
        parser.add_argument("prompt", nargs="+")
        parser.add_argument("-n", "--new", action="store_true")
        params = parser.parse_args(split_with_quotes(context.query))
        avatar = StableDiffusionAvatar(" ".join(params.prompt), params.new)
        path = avatar.path
        assert path
        assert path.exists()
        return RenderResult(
            method=ZMethod.AVATAR_AVATAR,
            attachment=Attachment(path=path.as_posix(), contentType=avatar.contentType),
        )
    except ArgumentError:
        return EmptyResult(
            method=ZMethod.AVATAR_AVATAR
        )
    except Exception as e:
        logging.info(e)
        return EmptyResult()


# # type: ignore
# @bp.command(method=ZMethod.AVATAR_RUSSIA, desc="generates avatar for the input")
# def avaru_command(context: Context) -> RenderResult:
#     avatar = Avataaar(context.query, "ru")
#     path = avatar.path
#     res = (
#         RenderResult(
#             method=ZMethod.AVATAR_RUSSIA,
#             attachment=Attachment(path=path.as_posix(),
#                                   contentType=avatar.contentType),
#         )
#         if path
#         else EmptyResult()
#     )
#     return res


# # type: ignore
# @bp.command(method=ZMethod.AVATAR_UKRAINE, desc="generates avatar for the input")
# def avauk_command(context: Context) -> RenderResult:
#     avatar = Avataaar(context.query, "uk")
#     path = avatar.path
#     res = (
#         RenderResult(
#             method=ZMethod.AVATAR_UKRAINE,
#             attachment=Attachment(path=path.as_posix(),
#                                   contentType=avatar.contentType),
#         )
#         if path
#         else EmptyResult()
#     )
#     return res

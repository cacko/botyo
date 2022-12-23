from botyo.api.logo.team import Team
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, RenderResult, EmptyResult
from botyo.api import ZMethod


bp = Blueprint("logo")


@bp.command(method=ZMethod.LOGO_TEAM, desc="logo for the requested football team")  # type: ignore
def logo_command(context: Context):
    logo = Team(context.query)
    path = logo.path
    if not path:
        return EmptyResult()
    res = RenderResult(
        attachment=Attachment(path=path.as_posix(), contentType=logo.contentType),
        method=ZMethod.LOGO_TEAM,
    )
    return res

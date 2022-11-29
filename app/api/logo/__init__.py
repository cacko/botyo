from app.api.logo.team import Team
from botyo_server.blueprint import Blueprint
from botyo_server.socket.connection import Context
from botyo_server.models import Attachment, RenderResult, EmptyResult
from app.api import ZMethod


bp = Blueprint("logo")


@bp.command(method=ZMethod.LOGO_TEAM, desc="logo for the requested football team")
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

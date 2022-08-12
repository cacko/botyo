from app.api.ontv.item.tv import TV
from botyo_server.blueprint import Blueprint
from app.api import ZMethod
from botyo_server.models import RenderResult, EmptyResult
from botyo_server.socket.connection import Context
from zoneinfo import ZoneInfo
from cachable.request import Request
from app.core.config import Config

bp = Blueprint("ontv")


@bp.command(
    method=ZMethod.ONTV_TV,
    desc="TV Schedule",
)
def tv_command(context: Context) -> RenderResult:
    tv = TV(
        Request(f"{Config.ontv.api_url}/data/schedule.json"),
        Config.ontv.leagues,
    )
    message = tv.render(
        filt=context.query,
        tz=ZoneInfo(context.timezone)
    )
    if not message:
        return EmptyResult()
    return RenderResult(
        message=message,
        method=ZMethod.ONTV_TV
    )

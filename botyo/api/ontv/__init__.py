from botyo.api.ontv.item.tv import TV
from botyo.server.blueprint import Blueprint
from botyo.server.models import ZMethod
from botyo.server.models import RenderResult, EmptyResult
from botyo.server.socket.connection import Context
from zoneinfo import ZoneInfo
from cachable.request import Request
from botyo.core.config import Config

bp = Blueprint("ontv")


@bp.command(
    method=ZMethod.ONTV_TV,
    desc="TV Schedule",
    icon="tv"
)  # type: ignore
def tv_command(context: Context) -> RenderResult:
    tv = TV(
        Request(f"{Config.ontv.api_url}/data/schedule.json"),
        Config.ontv.leagues,
    )
    assert context.timezone
    message = tv.render(filt=context.query, tz=ZoneInfo(context.timezone))
    if not message:
        return EmptyResult()
    return RenderResult(message=message, method=ZMethod.ONTV_TV)

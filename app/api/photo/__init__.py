from botyo_server.blueprint import Blueprint
from .fakeface import FakeFace
from app.api import ZMethod
from botyo_server.models import EmptyResult, RenderResult, Attachment
from botyo_server.socket.connection import Context

bp = Blueprint("photo")


@bp.command(
    method=ZMethod.PHOTO_FAKE,
    desc="fake photo"
)
def photo_command(context: Context):
    fakeface = FakeFace(context.query)
    path = fakeface.path

    if not path or not path.exists():
        return EmptyResult()

    res = RenderResult(
        attachment=Attachment(
            path=path.as_posix(),
            contentType=fakeface.contentType
        ),
        method=ZMethod.PHOTO_FAKE
    )

    return res

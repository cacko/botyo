from app.image import Image
from botyo_server.blueprint import Blueprint
from botyo_server.socket.connection import Context
from botyo_server.models import RenderResult, EmptyResult
from app.api import ZMethod
from stringcase import titlecase

bp = Blueprint("image")


@bp.command(
    method=ZMethod.IMAGE_ANALYZE,
    desc="Returns Emotion, Race, Gender, Age for image",
)  # type: ignore
def image_analyze(context: Context):
    attachment = context.attachment
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_ANALYZE)
    attachment, message = Image.analyze(attachment)
    if all([attachment is None, message is None]):
        return RenderResult(
            message="No matches",
            method=ZMethod.IMAGE_ANALYZE,
        )
    return RenderResult(
        message=message,
        attachment=attachment,
        method=ZMethod.IMAGE_ANALYZE,
    )


@bp.command(
    method=ZMethod.IMAGE_TAG,
    desc="tag faces in image",
)  # type: ignore
def image_Tag(context: Context):
    attachment = context.attachment
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_TAG)
    attachment, message = Image.tag(attachment)
    if all([attachment is None, message is None]):
        return RenderResult(
            message="No matches",
            method=ZMethod.IMAGE_TAG,
        )
    return RenderResult(
        message=message,
        attachment=attachment,
        method=ZMethod.IMAGE_TAG,
    )


@bp.command(
    method=ZMethod.IMAGE_HOWCUTE,
    desc="howcute faces in image",
)  # type: ignore
def image_howcute(context: Context):
    attachment = context.attachment
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_HOWCUTE)
    attachment, message = Image.howcute(attachment)
    if all([attachment is None, message is None]):
        return RenderResult(
            message="No matches",
            method=ZMethod.IMAGE_HOWCUTE,
        )
    return RenderResult(
        message=message,
        attachment=attachment,
        method=ZMethod.IMAGE_HOWCUTE,
    )


@bp.command(
    method=ZMethod.IMAGE_CLASSIFY,
    desc="Classify objects in images",
)  # type: ignore
def image_classify(context: Context):
    attachment = context.attachment
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_CLASSIFY)
    attachment, message = Image.classify(attachment)
    if message is None:
        return RenderResult(
            message="No matches",
            method=ZMethod.IMAGE_CLASSIFY,
        )
    return RenderResult(
        message="\n".join([titlecase(x.get("label")) for x in message.get("response")]),
        method=ZMethod.IMAGE_CLASSIFY,
    )


@bp.command(
    method=ZMethod.IMAGE_PIXEL,
    desc="pixel image",
)  # type: ignore
def image_pixel(context: Context):
    attachment = context.attachment
    query = context.query
    try:
        query = int(query)
    except ValueError:
        query = 8
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_PIXEL)
    attachment, message = Image.pixel(attachment, query)
    if all([attachment is None, message is None]):
        return RenderResult(
            message="No shit",
            method=ZMethod.IMAGE_PIXEL,
        )
    return RenderResult(
        message=message,
        attachment=attachment,
        method=ZMethod.IMAGE_PIXEL,
    )


@bp.command(
    method=ZMethod.IMAGE_POLYGON,
    desc="polygon image",
)  # type: ignore
def image_polygon(context: Context):
    attachment = context.attachment
    query = context.query
    try:
        query = int(query)
    except ValueError:
        query = 800
    if not attachment:
        return EmptyResult(method=ZMethod.IMAGE_POLYGON)
    attachment, message = Image.polygon(attachment, query)
    if all([attachment is None, message is None]):
        return RenderResult(
            message="No shit",
            method=ZMethod.IMAGE_POLYGON,
        )
    return RenderResult(
        message=message,
        attachment=attachment,
        method=ZMethod.IMAGE_POLYGON,
    )

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
    try:
        attachment = context.attachment
        assert attachment
        attachment, message = Image.analyze(attachment)
        assert attachment and message
        return RenderResult(
            message=message,
            attachment=attachment,
            method=ZMethod.IMAGE_ANALYZE,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_ANALYZE)


@bp.command(
    method=ZMethod.IMAGE_TAG,
    desc="tag faces in image",
)  # type: ignore
def image_Tag(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, message = Image.tag(attachment)
        assert attachment and message
        return RenderResult(
            message=message,
            attachment=attachment,
            method=ZMethod.IMAGE_TAG,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TAG)


@bp.command(
    method=ZMethod.IMAGE_HOWCUTE,
    desc="howcute faces in image",
)  # type: ignore
def image_howcute(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, message = Image.howcute(attachment)
        assert attachment and message
        return RenderResult(
            message=message,
            attachment=attachment,
            method=ZMethod.IMAGE_HOWCUTE,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_HOWCUTE)


@bp.command(
    method=ZMethod.IMAGE_CLASSIFY,
    desc="Classify objects in images",
)  # type: ignore
def image_classify(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, message = Image.classify(attachment)
        assert message
        return RenderResult(
            message="\n".join(
                [titlecase(x.get("label"))
                 for x in message.get("response", [])]
            ),
            method=ZMethod.IMAGE_CLASSIFY,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_CLASSIFY)


@bp.command(
    method=ZMethod.IMAGE_PIXEL,
    desc="pixel image",
)  # type: ignore
def image_pixel(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        query = context.query
        try:
            assert query
            query = int(query)
        except (ValueError, AssertionError):
            query = 8
        attachment, message = Image.pixel(attachment, query)
        assert attachment and message
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_PIXEL,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_PIXEL)


@bp.command(
    method=ZMethod.IMAGE_POLYGON,
    desc="polygon image",
)  # type: ignore
def image_polygon(context: Context):
    attachment = context.attachment
    query = context.query
    try:
        assert query
        query = int(query)
    except (ValueError, AssertionError):
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
        attachment=attachment,
        method=ZMethod.IMAGE_POLYGON,
    )


@bp.command(
    method=ZMethod.IMAGE_VARIATION,
    desc="variation of image",
)  # type: ignore
def image_variation(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, _ = Image.variation(attachment)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_VARIATION,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_VARIATION)


@bp.command(
    method=ZMethod.IMAGE_POKEMON,
    desc="poklemon of image",
)  # type: ignore
def image_pokemon(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.pokemon(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_POKEMON,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_POKEMON)


@bp.command(
    method=ZMethod.INAGE_FROMTEXT,
    desc="text to image",
)  # type: ignore
def image_fromtext(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.fromtext(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.INAGE_FROMTEXT,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.INAGE_FROMTEXT)

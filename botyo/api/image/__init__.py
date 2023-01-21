from botyo.image import Image
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import RenderResult, EmptyResult
from botyo.server.models import ZMethod
from stringcase import titlecase
import logging

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
                [titlecase(x.get("label")) for x in message.get("response", [])]
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
        attachment, _ = Image.pixel(attachment, query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_PIXEL,
        )
    except AssertionError as e:
        logging.exception(e)
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
        attachment, _ = Image.variation(attachment, context.query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_VARIATION,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_VARIATION)


@bp.command(
    method=ZMethod.IMAGE_TXT2IMG,
    desc="text to image",
)  # type: ignore
def image_fromtext(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.txt2img(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2IMG,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2IMG)


@bp.command(
    method=ZMethod.IMAGE_IMG2IMG,
    desc="image of image",
)  # type: ignore
def image2image(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, _ = Image.img2img(attachment, context.query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_IMG2IMG,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_IMG2IMG)


@bp.command(
    method=ZMethod.IMAGE_PORTRAIT,
    desc="portrait generator",
)  # type: ignore
def image_portrait(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.portrait(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_PORTRAIT,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_PORTRAIT)

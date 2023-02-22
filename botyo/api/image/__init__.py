from botyo.image import Image
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import (
    RenderResult,
    EmptyResult,
    ApiError,
    ZMethod
)
from stringcase import titlecase
import logging
from corestring import to_int

bp = Blueprint("image")


@bp.command(
    method=ZMethod.IMAGE_ANALYZE,
    desc="Returns Emotion, Race, Gender, Age for image",
    upload=True,
    icon="settings_accessibility"
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
    upload=True,
    icon="fingerprint"
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
    upload=True,
    icon="thumb_up"
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
    upload=True,
    icon="data_object"
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
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_CLASSIFY,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_CLASSIFY)


@bp.command(
    method=ZMethod.IMAGE_PIXEL,
    desc="pixel image",
    upload=True,
    icon="pix"
)  # type: ignore
def image_pixel(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        query = context.query
        attachment, _ = Image.pixel(attachment, to_int(query, 8))
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_PIXEL,
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_PIXEL,
            message=e.message
        )
    except AssertionError as e:
        logging.exception(e)
        return EmptyResult(method=ZMethod.IMAGE_PIXEL)


@bp.command(
    method=ZMethod.IMAGE_POLYGON,
    desc="polygon image",
    upload=True,
    icon="hexagon"
)  # type: ignore
def image_polygon(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        query = context.query
        attachment, _ = Image.polygon(attachment, to_int(query, 800))
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_POLYGON,
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_POLYGON,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_POLYGON)


@bp.command(
    method=ZMethod.IMAGE_VARIATION,
    desc="variation of image",
    upload=True,
    icon="difference"
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
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_VARIATION,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_VARIATION)


@bp.command(
    method=ZMethod.IMAGE_TXT2IMG,
    desc="text to image",
    icon="brush"
)  # type: ignore
def image_fromtext(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2img(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2IMG,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2IMG,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2IMG)


@bp.command(
    method=ZMethod.IMAGE_IMG2IMG,
    desc="image of image",
    upload=True,
    icon="collections"
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
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_IMG2IMG,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_IMG2IMG)


@bp.command(
    method=ZMethod.IMAGE_GPS2IMG,
    desc="generates image for given gps coordinates",
    icon="satellite"
)  # type: ignore
def gps2Image(context: Context):
    try:
        query = context.query
        assert query
        attachment, msg = Image.gps2img(query)
        return RenderResult(
            attachment=attachment,
            message=msg,
            method=ZMethod.IMAGE_GPS2IMG,
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_GPS2IMG,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_GPS2IMG)


@bp.command(
    method=ZMethod.IMAGE_TXT2ALBUMART,
    desc="text to album cover",
    icon="album"
)  # type: ignore
def image_fromtext2albumart(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2albumart(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2ALBUMART,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2ALBUMART,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2IMG)


@bp.command(
    method=ZMethod.IMAGE_TXT2CLAY,
    desc="text to clay illustration",
    icon="palette"
)  # type: ignore
def image_fromtext2clay(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2clay(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2CLAY,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2CLAY,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2CLAY)


@bp.command(
    method=ZMethod.IMAGE_TXT2ICON,
    desc="text to flat icon design",
    icon="palette"
)  # type: ignore
def image_fromtext2icon(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2icon(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2ICON,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2ICON,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2ICON)


@bp.command(
    method=ZMethod.IMAGE_TXT2PAPER,
    desc="text to paper cut",
    icon="draw"
)  # type: ignore
def image_fromtext2paer(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2paper(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2PAPER,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2PAPER,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2PAPER)


@bp.command(
    method=ZMethod.IMAGE_TXT2INK,
    desc="text to ink punk illustation",
    icon="draw"
)  # type: ignore
def image_fromtext2ink(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2ink(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2INK,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2INK,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2INK)


@bp.command(
    method=ZMethod.IMAGE_TXT2ZOMBIE,
    desc="text to zombie image",
    icon="draw"
)  # type: ignore
def image_fromtext2zombie(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2zombie(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2ZOMBIE,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2ZOMBIE,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2ZOMBIE)


@bp.command(
    method=ZMethod.IMAGE_TXT2DISNEY,
    desc="text to modern disnety style image",
    icon="draw"
)  # type: ignore
def image_fromtext2disney(context: Context):
    try:
        query = context.query
        assert query
        attachment, message = Image.txt2disney(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2DISNEY,
            message=message
        )
    except ApiError as e:
        return EmptyResult(
            method=ZMethod.IMAGE_TXT2DISNEY,
            message=e.message
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2DISNEY)

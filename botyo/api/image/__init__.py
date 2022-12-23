from botyo.image import Image
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import RenderResult, EmptyResult
from botyo.server.models import ZMethod
from botyo.core import to_int
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
        scale = to_int(context.query) if context.query else None
        attachment, _ = Image.variation(attachment, scale)
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
    method=ZMethod.IMAGE_TXT2ANYTHING,
    desc="text to anything",
)  # type: ignore
def text_to_antyhing(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.txt2anything(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2ANYTHING,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2ANYTHING)


@bp.command(
    method=ZMethod.IMAGE_TXT2ARCANE,
    desc="text to arcane",
)  # type: ignore
def text_to_arcane(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.txt2arcane(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2ARCANE,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2ARCANE)


@bp.command(
    method=ZMethod.IMAGE_TXT2DISNEY,
    desc="text to disney image",
)  # type: ignore
def text_to_disney(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.txt2disney(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2DISNEY,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_TXT2DISNEY)


@bp.command(
    method=ZMethod.IMAGE_MUTANT,
    desc="text to mutant",
)  # type: ignore
def image_mutant(context: Context):
    try:
        query = context.query
        assert query
        attachment, _ = Image.mutant(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_MUTANT,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_MUTANT)


@bp.command(
    method=ZMethod.IMAGE_IMG2DISNEY,
    desc="image of disney image",
)  # type: ignore
def image2disney(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, _ = Image.img2disney(attachment, context.query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_IMG2DISNEY,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_IMG2DISNEY)


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
    method=ZMethod.IMAGE_IMG2ANYTHING,
    desc="image of anything",
)  # type: ignore
def image2anything(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, _ = Image.img2anything(attachment, context.query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_IMG2ANYTHING,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_IMG2ANYTHING)


@bp.command(
    method=ZMethod.IMAGE_IMG2ARCANE,
    desc="image of arcane",
)  # type: ignore
def image2arcane(context: Context):
    try:
        attachment = context.attachment
        assert attachment
        attachment, _ = Image.img2arcane(attachment, context.query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_IMG2ARCANE,
        )
    except AssertionError:
        return EmptyResult(method=ZMethod.IMAGE_IMG2ARCANE)

import json

from botyo.image import Image
from botyo.image.models import Upload2Wallies
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import (
    RenderResult,
    ErrorResult,
    ApiError,
    ZMethod,
    ZSONOption,
    ClassifyResult
)
from stringcase import titlecase
import logging
from corestring import to_int

bp = Blueprint("image")


# @bp.command(
#     method=ZMethod.IMAGE_ANALYZE,
#     desc="Returns Emotion, Race, Gender, Age for image",
#     upload=True,
#     icon="settings_accessibility"
# )  # type: ignore
# def image_analyze(context: Context):
#     try:
#         attachment = context.attachment
#         assert attachment
#         attachment, message = Image.analyze(attachment)
#         assert attachment and message
#         return RenderResult(
#             message=message,
#             attachment=attachment,
#             method=ZMethod.IMAGE_ANALYZE,
#         )
#     except AssertionError:
#         return ErrorResult(method=ZMethod.IMAGE_ANALYZE)


# @bp.command(
#     method=ZMethod.IMAGE_TAG,
#     desc="tag faces in image",
#     upload=True,
#     icon="fingerprint"
# )  # type: ignore
# def image_Tag(context: Context):
#     try:
#         attachment = context.attachment
#         assert attachment
#         attachment, message = Image.tag(attachment)
#         assert attachment and message
#         return RenderResult(
#             message=message,
#             attachment=attachment,
#             method=ZMethod.IMAGE_TAG,
#         )
#     except AssertionError:
#         return ErrorResult(method=ZMethod.IMAGE_TAG)


# @bp.command(
#     method=ZMethod.IMAGE_HOWCUTE,
#     desc="howcute faces in image",
#     upload=True,
#     icon="thumb_up"
# )  # type: ignore
# def image_howcute(context: Context):
#     try:
#         attachment = context.attachment
#         assert attachment
#         attachment, message = Image.howcute(attachment)
#         assert attachment and message
#         return RenderResult(
#             message=message,
#             attachment=attachment,
#             method=ZMethod.IMAGE_HOWCUTE,
#         )
#     except AssertionError:
#         return ErrorResult(method=ZMethod.IMAGE_HOWCUTE)


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
        logging.debug(attachment)
        attachment, message = Image.classify(attachment)
        assert message
        results = [ClassifyResult(**x) for x in message.get("response", [])]
        return RenderResult(
            message="\n".join(
                [f"{titlecase(x.label)} - {x.score}" for x in results if x.score < 1]
            ),
            method=ZMethod.IMAGE_CLASSIFY,
        )
    except ApiError as e:
        return ErrorResult(
            method=ZMethod.IMAGE_CLASSIFY,
            message=e.message
        )
    except AssertionError:
        return ErrorResult(method=ZMethod.IMAGE_CLASSIFY)


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
        return ErrorResult(
            method=ZMethod.IMAGE_PIXEL,
            message=e.message
        )
    except AssertionError as e:
        logging.exception(e)
        return ErrorResult(method=ZMethod.IMAGE_PIXEL)


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
        return ErrorResult(
            method=ZMethod.IMAGE_VARIATION,
            message=e.message
        )
    except AssertionError:
        return ErrorResult(method=ZMethod.IMAGE_VARIATION)


@bp.command(
    method=ZMethod.IMAGE_TXT2IMG,
    desc="text to image",
    icon="brush",
    uses_prompt=True,
    options=[
        ZSONOption(option="-m", choices=Image.options.model),
        ZSONOption(option="-r", choices=Image.options.resolution),
        ZSONOption(option="-t", choices=Image.options.template)
    ]
)  # type: ignore
def image_fromtext(context: Context):
    try:
        query = context.query
        Image.is_admin = context.is_admin
        assert query
        attachment, _ = Image.txt2img(query)
        assert attachment
        return RenderResult(
            attachment=attachment,
            method=ZMethod.IMAGE_TXT2IMG,
            # message=message
        )
    except ApiError as e:

        logging.error(e)
        return RenderResult(
            method=ZMethod.IMAGE_TXT2IMG,
            message=Image.image_generator_parser.format_help()
        )
    except AssertionError as e:
        logging.error(e)
        return RenderResult(
            method=ZMethod.IMAGE_TXT2IMG,
            message=Image.image_generator_parser.format_help()
        )


@bp.command(
    method=ZMethod.IMAGE_UPLOAD2WALLIES,
    admin=True
)  # type: ignore
def upload2wallies(context: Context):
    try:
        query = context.query
        assert query
        params = Upload2Wallies.parse_raw(query)
        message = Image.upload2wallies(params=params)
        assert message
        return RenderResult(
            message=json.dumps(message),
            method=ZMethod.IMAGE_UPLOAD2WALLIES,
        )
    except AssertionError:
        return RenderResult(method=ZMethod.IMAGE_UPLOAD2WALLIES)
    except ApiError:
        return ErrorResult(
            error="Already uploaded",
            method=ZMethod.IMAGE_UPLOAD2WALLIES
        )


@bp.command(
    method=ZMethod.IMAGE_GPS2IMG,
    desc="generates image for given gps coordinates",
    icon="satellite",
    uses_prompt=True
)  # type: ignore
def gps2Image(context: Context):
    try:
        query = context.query
        assert query
        Image.is_admin = context.is_admin
        attachment, msg = Image.gps2img(query)
        return RenderResult(
            attachment=attachment,
            message=msg,
            method=ZMethod.IMAGE_GPS2IMG,
        )
    except ApiError as e:
        return ErrorResult(
            method=ZMethod.IMAGE_GPS2IMG,
            message=e.message
        )
    except AssertionError:
        return ErrorResult(method=ZMethod.IMAGE_GPS2IMG)

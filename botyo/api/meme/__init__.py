from botyo.meme.imgflip import ImgFlip
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import Attachment, RenderResult, EmptyResult
from botyo.server.models import ZMethod
from botyo.core.image import download_image

bp = Blueprint("meme")


@bp.command(
    method=ZMethod.MEME_CAPTION,
    desc="Meme captioning",
    icon="format_quote"
)  # type: ignore
def meme_caption_command(context: Context):
    try:
        assert context.query
        meme = ImgFlip.caption(context.query)
        assert meme.data
        assert meme.data.url
        tmp_file = download_image(meme.data.url)
        res = RenderResult(
            attachment=Attachment(
                path=tmp_file.as_posix(),
                contentType="image/jpeg"
            ),
            method=ZMethod.MEME_CAPTION,
        )
        return res
    except AssertionError:
        return EmptyResult(method=ZMethod.MEME_CAPTION)

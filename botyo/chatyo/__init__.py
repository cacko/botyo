import logging
from uuid import uuid4
from cachable.storage.file import FileStorage
from cachable.request import Request, Method
from botyo.core.config import Config
from typing import Optional
from botyo.server.models import Attachment
from pydantic import BaseModel


class Payload(BaseModel):
    message: str
    source: Optional[str] = None
    lang: Optional[str] = None
    detect_lang: Optional[bool] = None


class Response(BaseModel):
    response: str
    attachment: Optional[Attachment]


def getResponse(path: str, payload: Payload) -> Response:
    url = f"{Config.chatyo.base_url}/{path}"
    req = Request(
        url,
        Method.POST,
        json=payload.model_dump()  # type: ignore
    )
    message = ""
    attachment = None
    if req.is_multipart:
        cp = FileStorage.storage_path
        multipart_data = req.multipart
        for part in multipart_data.parts:
            content_type = part.headers.get(
                b"content-type", b"").decode()  # type: ignore
            logging.debug(f"Multipart part content-type: {content_type}")
            match content_type:
                case "image/png":
                    fp = cp / f"{uuid4().hex}.png"
                    fp.write_bytes(part.content)
                    attachment = Attachment(path=fp.absolute().as_posix(),
                                            contentType="image/png", )
                case "image/jpeg":
                    fp = cp / f"{uuid4().hex}.jpg"
                    fp.write_bytes(part.content)
                    attachment = Attachment(path=fp.absolute().as_posix(),
                                            contentType="image/jpeg", )
                case _:
                    logging.debug(f"multipart text={part.text}")
                    message = part.text
    else:
        msg = req.json
        if msg:
            message = msg.get("response", "")
    return Response(
        response=message,
        attachment=attachment
    )

from dataclasses import dataclass
import logging
from uuid import uuid4
from cachable import Cachable
from cachable.request import Request, Method
from dataclasses_json import dataclass_json
from app.core.config import Config
from typing import Optional
from botyo_server.models import Attachment

@dataclass_json()
@dataclass()
class Payload:
    message: str
    source: Optional[str] = None
    lang: Optional[str] = None


@dataclass_json()
@dataclass()
class Response:
    response: str
    attachment: Optional[Attachment]


def getResponse(path: str, payload: Payload) -> Response:
    url = f"{Config.chatyo.base_url}/{path}"
    req = Request(
        url,
        Method.POST,
        json=payload.to_dict()
    )
    message = ""
    attachment = None
    is_multipart = req.is_multipart
    if is_multipart:
        cp = Cachable.storage
        multipart_data = req.multipart
        for part in multipart_data.parts:
            content_type = part.headers.get(b"content-type", b"").decode()
            logging.debug(f"Multipart part content-type: {content_type}")
            if "image/png" in content_type:
                fp = cp / f"{uuid4().hex}.png"
                fp.write_bytes(part.content)
                attachment = Attachment(path=fp.absolute().as_posix(),
                                        contentType="image/png", )
            elif "image/jpeg" in content_type:
                fp = cp / f"{uuid4().hex}.jpg"
                fp.write_bytes(part.content)
                attachment = Attachment(path=fp.absolute().as_posix(),
                                        contentType="image/jpeg", )
            else:
                message = part.text
    else:
        message = req.json
        if message:
            message = message.get("response")
    return Response(
        response=message,
        attachment=attachment
    )

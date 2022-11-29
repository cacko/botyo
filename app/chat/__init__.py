from app.chatyo import Payload, Response, getResponse
from typing import Optional

class ChatMeta(type):

    _instance = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def dialog(cls, source, text, lang: Optional[str] = None) -> Response:
        return cls().getResponse("chat/dialog", text, source, lang)

    def phrase(cls, text, source=None, lang: Optional[str] = None) -> Response:
        return cls().getResponse("chat/phrase", text, source, lang)

    def reply(cls, text, source=None, lang: Optional[str] = None) -> Response:
        return cls().getResponse("chat/sarcastic", text, source, lang)

class Chat(object, metaclass=ChatMeta):

    def getResponse(
            self,
            path,
            text,
            source: Optional[str] = None,
            lang: Optional[str] = None) -> Response:
        return getResponse(
            path,
            Payload(
                message=text,
                source=source,
                lang=lang,
            )
        )

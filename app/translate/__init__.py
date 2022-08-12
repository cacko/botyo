from app.chatyo import Payload, getResponse


class TranslateMeta(type):

    _instance = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def translate(cls, lang, text) -> str:
        return cls().getResponse(f"trans/{lang}", text)


class Translate(object, metaclass=TranslateMeta):

    def getResponse(self, path, text) -> str:
        return getResponse(
            path,
            Payload(
                message=text,
            )
        )

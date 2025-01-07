from botyo.chatyo import Payload, Response, getResponse


class CodeMeta(type):

    _instance = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def php(cls, text) -> Response:
        return cls().getResponse("code/instruct/php", text)

    def python(cls, text) -> Response:
        return cls().getResponse("code/instruct/python", text)

    def javascript(cls, text) -> Response:
        return cls().getResponse("code/instruct/javascript", text)
    
    def general(cls, text) -> Response:
        return cls().getResponse("code/instruct/general", text)



class Code(object, metaclass=CodeMeta):
    def getResponse(self, path, text) -> Response:
        return getResponse(path, Payload(message=text))

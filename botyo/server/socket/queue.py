from queue import Queue as PyQueue, Empty
from time import sleep


class QueueMeta(type):

    __instance = None

    def __call__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwargs)
        return cls.__instance

    def register(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def put_data(cls, *args, **kwargs):
        return cls().put_nowait(*args, **kwargs)

    def data(cls, *args, **kwargs):
        while True:
            try:
                data = cls().get_nowait()
                if data:
                    yield data
            except Empty:
                sleep(0.05)

    @property
    def isEmpty(cls):
        return cls().empty()


class Queue(PyQueue, metaclass=QueueMeta):
    pass

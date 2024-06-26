from cachable.storage.redis import RedisStorage
from cachable.storage.file import FileStorage
from cachable.storage.filestorage.image import CachableFileImage
from cachable import TimeCacheable as MainTimeCachable, Cachable
import pickle
import logging
from typing import Any


class QueueDictMeta(type):

    __instances = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds
            )
        return cls.__instances[storage_key]


class QueueDict(dict, metaclass=QueueDictMeta):

    __storage_key: str

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        items = self.load()
        super().__init__(items, *args, **kwds)

    def load(self) -> dict[str, Any]:
        try:
            data = RedisStorage.hgetall(self.__storage_key)
            if not data:
                return {}
            items = {k.decode(): self.loads(v) for k, v in data.items()}
            return items
        except Exception as e:
            logging.error(e)
        return {}

    def __setitem__(self, __k, __v) -> None:
        RedisStorage.pipeline().hset(
            self.__storage_key, __k, self.dumps(__v)
        ).persist(
            self.__storage_key
        ).execute()
        return super().__setitem__(__k, __v)

    def __delitem__(self, __k) -> None:
        RedisStorage.pipeline().hdel(
            self.__storage_key, __k
        ).persist(
            self.__storage_key
        ).execute()
        return super().__delitem__(__k)

    def dumps(self, v):
        return pickle.dumps(v)

    def loads(self, v):
        return pickle.loads(v)


class QueueListMeta(type):

    __instances: dict[str, 'QueueList'] = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds
            )
        return cls.__instances[storage_key]


class QueueList(list, metaclass=QueueListMeta):

    __storage_key: str

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        items = self.load()
        super().__init__(items, *args, **kwds)

    def append(self, __object: Any) -> None:
        RedisStorage.pipeline().sadd(self.__storage_key, self.dumps(__object)).persist(
            self.__storage_key
        ).execute()
        return super().append(__object)

    def remove(self, __value: Any) -> None:
        RedisStorage.pipeline().srem(self.__storage_key, self.dumps(__value)).persist(
            self.__storage_key
        ).execute()
        return super().remove(__value)

    def dumps(self, v):
        return pickle.dumps(v)

    def loads(self, v):
        return pickle.loads(v)

    def load(self) -> list[Any]:
        data = RedisStorage.smembers(self.__storage_key)
        if not data:
            logging.debug("no data")
            return []
        items = [self.loads(v) for v in data]
        return list(items)


class RedisCachable(Cachable):
    @property
    def storage(self):
        return RedisStorage()


class TimeCachable(MainTimeCachable):
    @property
    def storage(self):
        return RedisStorage()


class ImageCachable(CachableFileImage):
    @property
    def storage(self):
        return FileStorage()


class FileCachable(Cachable):
    @property
    def storage(self):
        return FileStorage()

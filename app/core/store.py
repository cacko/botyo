from cachable.storage.redis import RedisStorage
import pickle
import logging
from typing import Any


class Storage(RedisStorage):
    @classmethod
    def hmset(cls, name: str, mapping: dict):
        return cls._redis.hmset(name, mapping)


class QueueDictMeta(type):

    __instances = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds
            )
        return cls.__instances[storage_key]

    def _load(cls, storage_key) -> dict[str, Any]:
        data = Storage.hgetall(storage_key)
        if not data:
            logging.debug("no data")
            return {}
        items = {k.decode(): pickle.loads(v) for k, v in data.items()}
        return items


class QueueDict(dict, metaclass=QueueDictMeta):

    __storage_key: str

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        items = __class__._load(storage_key)
        super().__init__(items, *args, **kwds)

    def __setitem__(self, __k, __v) -> None:
        Storage.pipeline().hset(self.__storage_key, __k, pickle.dumps(__v)).persist(
            self.__storage_key
        ).execute()
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        Storage.pipeline().hdel(self.__storage_key, __v).persist(
            self.__storage_key
        ).execute()
        return super().__delitem__(__v)



class QueueListMeta(type):

    __instances = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds
            )
        return cls.__instances[storage_key]

    def _load(cls, storage_key) -> list[Any]:
        data = Storage.smembers(storage_key)
        if not data:
            logging.debug("no data")
            return []
        items = [pickle.loads(v) for k, v in data]
        return list(items)


class QueueList(list, metaclass=QueueDictMeta):

    __storage_key: str

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        items = __class__._load(storage_key)
        super().__init__(items, *args, **kwds)

    def __setitem__(self, __k, __v) -> None:
        Storage.pipeline().sadd(self.__storage_key, pickle.dumps(__v)).persist(
            self.__storage_key
        ).execute()
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        Storage.pipeline().srem(self.__storage_key, pickle.dumps(__v)).persist(
            self.__storage_key
        ).execute()
        return super().__delitem__(__v)
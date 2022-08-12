from cachable.storage import Storage as MetaStorage


class Storage(MetaStorage):

    @classmethod
    def hmset(cls, name: str, mapping: dict):
        if cls._bypass:
            return None
        return cls._redis.hmset(name, mapping)

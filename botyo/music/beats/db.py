from peewee import *
from playhouse.db_url import connect, parse
from playhouse.postgres_ext import *
from botyo.core.config import Config as app_config

class BeatsDbMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    @property
    def db(cls) -> PostgresqlExtDatabase:
        return cls().get_db()


class BeatsDb(object, metaclass=BeatsDbMeta):
    __db: PostgresqlExtDatabase = None

    def __init__(self):
        config = app_config.beats
        parsed = parse(config.db_url)
        self.__db = PostgresqlExtDatabase(**parsed)

    def get_db(self) -> PostgresqlExtDatabase:
        return self.__db

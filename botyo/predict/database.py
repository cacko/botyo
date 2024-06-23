import logging
from playhouse.db_url import parse
from playhouse.postgres_ext import PostgresqlExtDatabase
from typing import Optional, Any
import os
from peewee import OperationalError
from termo_service.config import app_config

class ReconnectingDB(PostgresqlExtDatabase):
    
    def execute_sql(self, sql, params: Any | None = ..., commit=...):
        try:
            return super().execute_sql(sql, params, commit)
        except OperationalError as e:
            logging.error(e)


class DatabaseMeta(type):
    _instance: Optional['Database'] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    @property
    def db(cls) -> ReconnectingDB:
        return cls().get_db()


class Database(object, metaclass=DatabaseMeta):

    def __init__(self):
        parsed = parse(app_config.db.url)
        self.__db = ReconnectingDB(**parsed)

    def get_db(self) -> ReconnectingDB:
        return self.__db

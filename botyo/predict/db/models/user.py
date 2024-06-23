from enum import unique
from typing import Literal

from psycopg2 import IntegrityError
from botyo.predict.db.database import Database
from .base import DbModel
from peewee import CharField

class User(DbModel):
    phone = CharField(null=False, unique=True)
    name = CharField(null=True)
    
    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["User", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        phone = kwargs.get("phone")
        query = query.where((cls.phone == phone))

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                if defaults:
                    kwargs.update(defaults)
                return cls.create(**kwargs), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    class Meta:
        database = Database.db
        table_name = "predict_user"

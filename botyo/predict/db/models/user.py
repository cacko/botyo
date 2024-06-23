from enum import unique
from typing import Literal
from botyo.predict.db.database import Database
from .base import DbModel
from peewee import CharField

class User(DbModel):
    phone = CharField(null=False, unique=True)
    name = CharField()

    class Meta:
        database = Database.db
        table_name = "predict_user"

import logging

from botyo.predict.db.database import Database
from .base import DbModel
from peewee import CharField, DateTimeField, fn
from playhouse.shortcuts import model_to_dict
from datetime import timezone, datetime, timedelta

class User(DbModel):
    phone = CharField(null=False)
    name = CharField()

    class Meta:
        database = Database.db
        table_name = "predict_user"
        indexes = ((("phone",), True),)

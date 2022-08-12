__all__ = ["BaseModel"]

from peewee import *
from app.music.beats.db import BeatsDb
from playhouse.shortcuts import model_to_dict


class BaseModel(Model):
    @classmethod
    def fetch(cls, *query, **filters):
        try:
            return cls.get(*query, **filters)
        except cls.DoesNotExist:
            return None

    def to_dict(self):
        return model_to_dict(self)

    class Meta:
        database = BeatsDb.db

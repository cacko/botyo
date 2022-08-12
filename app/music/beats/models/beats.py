from peewee import *
from . import BaseModel
from playhouse.postgres_ext import JSONField


class Beats(BaseModel):
    path = CharField(index=True)
    path_id = CharField(max_length=40, unique=True, index=True)
    beats = JSONField()
    tempo = FloatField()

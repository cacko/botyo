from enum import unique

from psycopg2 import IntegrityError
from botyo.predict.db.database import Database
from .base import DbModel
from peewee import CharField, DateTimeField, IntegerField

class Game(DbModel):
    id_event = IntegerField(null=False, unique=True)
    league_id = IntegerField(null=False)
    home_team_id = IntegerField(null=False)
    away_team_id =  IntegerField(null=False)
    status = CharField()
    start_time = DateTimeField()
    home_score = IntegerField(default=-1)
    away_score = IntegerField(default=-1)
    
    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Game", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        id_event = kwargs.get("id_event")
        query = query.where((cls.id_event == id_event))

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
        table_name = "predict_game"

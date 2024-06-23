from enum import unique
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

    class Meta:
        database = Database.db
        table_name = "predict_game"

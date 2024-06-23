from botyo.predict.db.database import Database
from .base import DbModel
from .user import User
from .game import Game
from peewee import CharField, TimestampField, ForeignKeyField

class Prediction(DbModel):
    User = ForeignKeyField(User)
    Game = ForeignKeyField(Game)
    prediction = CharField()
    timestamp = TimestampField()

    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

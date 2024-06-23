from telnetlib import GA

from psycopg2 import IntegrityError
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
    
    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Game", bool]:
        defaults = kwargs.pop("defaults", {})
        game: Game = kwargs.get("Game")
        user: User = kwargs.get("User")
        query = cls.select().join(Game).join(User)
        query = query.where(
            (Game.id_event == game.id) & (User.phone == user.phone)
        )
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
                
    @classmethod
    def get_in_progress(cls, **kwargs):
        pass
        # user: User = kwargs.get("User")
        # query = cls.select().join(Game).join(User)
        # query = query.where(
        #     (Game.start_time == game.id) & (User.phone == user.phone)
        # )    

    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

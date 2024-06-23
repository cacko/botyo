from telnetlib import GA
from venv import logger
from datetime import datetime, timezone
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
    def get_or_create(cls: "Prediction", **kwargs) -> tuple["Prediction", bool]:
        defaults = kwargs.pop("defaults", {})
        game: Game = kwargs.get("Game")
        user: User = kwargs.get("User")
        query = cls.select().join_from(Prediction, Game).join_from(Prediction, User)
        query = query.where(
            (Game.id_event == game.id_event) & (User.phone == user.phone)
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
        user: User = kwargs.get("User")
        query = cls.select().join_from(Prediction, Game).join_from(Prediction, User)
        # query = query.where(
        #     (Game.start_time == game.id) & (User.phone == user.phone)
        # )

    @property
    def can_predict(self) -> bool:
        logger.warning(
            [self.Game.start_time, datetime.now(tz=timezone.utc), self.Game.status]
        )

    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

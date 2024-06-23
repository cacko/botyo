from _typeshed import Incomplete
import logging
from telnetlib import GA
from typing import Any, Generator, Optional
from venv import logger
from datetime import datetime, timezone
from psycopg2 import IntegrityError
from botyo.api.footy.item.components import ScoreRow
from botyo.predict.db import PredictionNotAllow
from botyo.predict.db.database import Database
from botyo.threesixfive.item.models import GameStatus
from .base import DbModel
from .user import User
from .game import Game
from peewee import CharField, TimestampField, ForeignKeyField, fn


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
    def get_in_progress(cls, **kwargs) -> Generator["Prediction", None, None]:
        user: User = kwargs.get("User")
        query = cls.select().join_from(Prediction, Game).join_from(Prediction, User)
        query = query.where(
            (fn.DATE(Game.start_time) == fn.CURRENT_DATE) & (User.phone == user.phone)
        )
        yield from query

    @classmethod
    def update(cls, data: Optional[Any], **update):
        game: Optional[Game] = update.get("Game")
        try:
            assert isinstance(data, dict)
            assert "Game" in data
            game: Game = data.get("Game")
        except AssertionError:
            pass

        try:
            assert game
            assert game.can_predict
            return super().update(data, **update)
        except Exception as e:
            logging.exception(e)

    @classmethod
    def insert(cls, data: Incomplete | None = ..., /, **insert):
        game: Optional[Game] = insert.get("Game")
        try:
            assert isinstance(data, dict)
            assert "Game" in data
            game: Game = data.get("Game")
        except AssertionError:
            pass
        try:
            assert game
            assert game.can_predict
            return super().insert(data, **insert)
        except Exception as e:
            logging.exception(e)

    @property
    def can_predict(self) -> bool:
        return self.Game.canPredict

    @property
    def score_row(self) -> ScoreRow:
        p_hscore, p_ascore = map('int', self.prediction.split(":"))
        return ScoreRow(
            id_event=self.Game.id_event,
            league_id=self.Game.league_id,
            home_team_id=self.Game.home_team_id,
            away_team_id=self.Game.away_team_id,
            status=self.Game.status,
            start_time=self.Game.start_time,
            home_score=p_hscore,
            away_score=p_ascore,
        )

    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

from datetime import datetime, timezone
import logging
from typing import Any, Generator, Optional
from numpy import mat
from psycopg2 import IntegrityError
from botyo.api.footy.item.components import PredictionRow, ScoreRow
from botyo.threesixfive.item.models import Competitor
from botyo.predict.db.database import Database
from .base import DbModel
from .user import User
from .game import Game
from peewee import CharField, TimestampField, ForeignKeyField, fn, Query
import re

PREDICTION_PATTERN = re.compile(r"(\d+)[^\d](\d+)")

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
        query = Prediction.select().join_from(Prediction, Game).join_from(Prediction, User)
        query: Query = query.where(
            (fn.date(Game.start_time) == datetime.now(tz=timezone.utc).date()) & (User.phone == user.phone)
        )
        yield from query.execute()

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
    def insert(cls, data: Optional[Any]= None, **insert):
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
    
    def save(self, force_insert: bool = ..., only: Any | None = ...):
        home_score, away_score = PREDICTION_PATTERN.findall(self.prediction.strip())
        self.prediction = f"{home_score}:{away_score}"
        return super().save(force_insert, only)

    @property
    def can_predict(self) -> bool:
        return self.Game.canPredict
    
    @property
    def HomeTeam(self) -> Competitor:
        return self.Game.home_team
    
    @property
    def AwayTeam(self) -> Competitor:
        return self.Game.away_team
    
    @property
    def score(self) -> str:
        return self.Game.score

    @property
    def prediction_row(self) -> PredictionRow:
        return PredictionRow(
            status=self.Game.status,
            home=self.HomeTeam.name,
            away=self.AwayTeam.name,
            score=self.Game.score,
            prediction=self.prediction,
            league = "",
        )
        
    def points(self) -> int:
        home_goals, away_goals = map("int", self.prediction.split(":"))
        if all([home_goals == self.Game.home_score, away_goals == self.Game.away_score]):
            return 3
        pdiff = home_goals - away_goals
        gdiff = self.Game.home_score - self.Game.away_score
        match pdiff:
            case 0:
                return 1 if gdiff == 0 else 0
            case pdiff if pdiff > 0:
                return 1 if gdiff > 0 else 0
            case pdiff if pdiff < 0:
                return 1 if gdiff < 0 else 0
        


    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

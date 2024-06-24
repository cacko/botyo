from datetime import datetime, timezone
import logging
from telnetlib import GA
from typing import Any, Generator, Optional
from numpy import mat
from psycopg2 import IntegrityError
from botyo.api.footy.item.components import PredictionRow
from botyo.threesixfive.item.models import Competitor, GameStatus
from botyo.predict.db.database import Database
from .base import DbModel
from .user import User
from .game import Game
from peewee import (
    CharField,
    TimestampField,
    ForeignKeyField,
    fn,
    Query,
    prefetch,
    BooleanField,
)
from corestring import to_int
import re

PREDICTION_PATTERN = re.compile(r"(\d+)[^\d](\d+)")


class Prediction(DbModel):
    User = ForeignKeyField(User)
    Game = ForeignKeyField(Game)
    prediction = CharField()
    timestamp = TimestampField()
    calculated = BooleanField(default=False)

    def on_ended(self):
        try:
            assert self.Game.ended
            self.User.add_points(self.points)
            self.calculated = True
            self.save(only=["calculated"])
            return self
        except AssertionError:
            pass
        return None

    @classmethod
    def get_or_create(cls: "Prediction", **kwargs) -> tuple["Prediction", bool]:
        defaults = kwargs.pop("defaults", {})
        game: Game = kwargs.get("Game")
        user: User = kwargs.get("User")
        game = game.update_miss()
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
    def calculate_missing(cls, **kwargs) -> Generator["Prediction", None, None]:
        query = (
            Prediction.select(Prediction, Game, User)
            .join_from(Prediction, Game)
            .join_from(Prediction, User)
        ).where(
            (Prediction.calculated == False) &
            (Game.status.in_([GameStatus.FT.value, GameStatus.AET.value]))
        )
        yield from prefetch(query, Game, User)
        

    @classmethod
    def get_in_progress(cls, **kwargs) -> Generator["Prediction", None, None]:
        user: User = kwargs.get("User")
        query = (
            Prediction.select(Prediction, Game, User)
            .join_from(Prediction, Game)
            .join_from(Prediction, User)
        )
        query: Query = query.where(
            (fn.date(Game.start_time) == datetime.now(tz=timezone.utc).date())
            & (User.phone == user.phone)
        )
        yield from prefetch(query, Game, User)

    def save(self, force_insert=False, only=None):
        try:
            assert self.Game
            assert self.can_predict
            home_score, away_score = PREDICTION_PATTERN.findall(
                self.prediction.strip()
            ).pop(0)
            self.prediction = f"{home_score}:{away_score}"
            return super().save(force_insert, only)
        except AssertionError:
            pass
        return None

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
        return self.Game.result

    @property
    def status(self) -> str:
        return self.Game.status

    @property
    def prediction_row(self) -> PredictionRow:
        self.Game = self.Game.update_miss()
        return PredictionRow(
            status=self.status,
            home=self.HomeTeam.name,
            away=self.AwayTeam.name,
            score=self.score,
            prediction=self.prediction,
            points=self.points,
            league="",
        )

    @property
    def points(self) -> int:
        home_goals, away_goals = map(
            lambda g: to_int(g, default=-1), self.prediction.split(":")
        )
        assert any([home_goals != -1, away_goals != -1])
        if all(
            [home_goals == self.Game.home_score, away_goals == self.Game.away_score]
        ):
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

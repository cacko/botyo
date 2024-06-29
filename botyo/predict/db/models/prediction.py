from datetime import datetime, timezone
import logging
from typing import Any, Generator, Optional
from venv import create
from psycopg2 import IntegrityError
from botyo.api.footy.item.components import PredictionRow
from botyo.threesixfive.item.models import Competitor, GameStatus, UpdateData
from botyo.predict.db.database import Database
from .base import DbModel, PredictionNotAllow
from .user import DbUser
from .game import DbGame
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


class DbPrediction(DbModel):
    User = ForeignKeyField(DbUser)
    Game = ForeignKeyField(DbGame)
    prediction = CharField()
    timestamp = TimestampField()
    calculated = BooleanField(default=False)

    def on_ended(self):
        try:
            assert self.Game.ended
            logging.warning(f"on _ended {self.points} {self}")
            # self.User.add_points(self.points)
            self.calculated = True
            self.save(only=["calculated"])
            return self
        except AssertionError:
            pass
        return None

    @classmethod
    def on_livescore_event(cls, data: UpdateData):
        logging.warn(data)
        game: DbGame = DbGame.get(DbGame.id_event == data.event_id)
        home_score, away_score = cls.goals(data.score_message)
        game.home_score = home_score
        game.away_score = away_score
        game.status = data.status
        game.save()
        if not game.ended:
            return
        for pred in DbPrediction.select().where(
            (DbPrediction.calculated == False) & (DbGame.id_event == game.id_event)
        ):
            pred.on_ended()

    @classmethod
    def get_or_create(cls: "DbPrediction", **kwargs) -> tuple["DbPrediction", bool]:
        defaults = kwargs.pop("defaults", {})
        game: DbGame = kwargs.get("Game")
        user: DbUser = kwargs.get("User")
        query = (
            cls.select(DbPrediction, DbGame, DbUser)
            .join_from(DbPrediction, DbGame)
            .join_from(DbPrediction, DbUser)
        )
        query = query.where(
            (DbGame.id_event == game.id_event) & (DbUser.phone == user.phone)
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
    def calculate_missing(cls, **kwargs) -> Generator["DbPrediction", None, None]:
        try:
            query = (
                DbPrediction.select(DbPrediction)
                .join_from(DbPrediction, DbGame)
                .join_from(DbPrediction, DbUser)
            ).where(
                (DbPrediction.calculated == False)
                & (DbGame.status.in_([GameStatus.FT.value, GameStatus.AET.value]))
            )
            yield from prefetch(query, DbGame, DbUser)            
            
        except Exception:
            return None


    @classmethod
    def get_in_progress(cls, **kwargs) -> Generator["DbPrediction", None, None]:
        try:
            user: DbUser = kwargs.get("User")
            query = (
                DbPrediction.select(DbPrediction)
                .join_from(DbPrediction, DbGame)
                .join_from(DbPrediction, DbUser)
            )
            query: Query = query.where(
                (fn.date(DbGame.start_time) == datetime.now(tz=timezone.utc).date())
                & (DbUser.phone == user.phone)
            )
            yield from prefetch(query, DbGame, DbUser)
        
        except Exception:
            return None

    def save(self, force_insert=False, only=None):
        try:
            assert self.Game
            assert self.can_predict
        except AssertionError as e:
            only: list[str] = self.dirty_fields
            only.remove("prediction")
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
    def score(self) -> Optional[str]:
        return self.Game.result

    @property
    def status(self) -> str:
        return self.Game.status

    @property
    def display_status(self) -> str:
        return self.Game.display_status

    @classmethod
    def goals(cls, prediction: str) -> tuple[int, int]:
        return tuple(
            map(
                lambda g: to_int(g, default=-1),
                PREDICTION_PATTERN.findall(prediction.strip()).pop(0),
            )
        )
        
    @property
    def display_prediction(self) -> str:
        return ":".join(map(str, DbPrediction.goals(self.prediction)))

    @property
    def prediction_row(self) -> PredictionRow:
        return PredictionRow(
            status=self.display_status,
            home=self.HomeTeam.name,
            away=self.AwayTeam.name,
            score=self.score,
            prediction=self.display_prediction,
            points=self.points,
            league="",
            is_international=self.Game.league.is_international,
        )

    @property
    def points(self) -> int:
        try:
            home_goals, away_goals = DbPrediction.goals(self.prediction)
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
        except AssertionError:
            return 0

    class Meta:
        database = Database.db
        table_name = "predict_prediction"
        indexes = ((("User",), False),)

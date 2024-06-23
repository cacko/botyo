import logging
import stat
from typing import Optional
from numpy import save
from psycopg2 import IntegrityError
from botyo.api.footy.item.subscription import UpdateData
from botyo.threesixfive.item.team import Team
from botyo.predict.db.database import Database
from botyo.threesixfive.item.competition import CompetitionData
from botyo.threesixfive.item.models import Competition, Competitor, GameStatus
from .base import DbModel, PredictionNotAllow
from peewee import CharField, DateTimeField, IntegerField
from datetime import datetime, timezone


class Game(DbModel):
    id_event = IntegerField(null=False, unique=True)
    league_id = IntegerField(null=False)
    home_team_id = IntegerField(null=False)
    away_team_id = IntegerField(null=False)
    status = CharField()
    start_time = DateTimeField()
    home_score = IntegerField(default=-1)
    away_score = IntegerField(default=-1)


    def save(self, force_insert=False, only=None):
        super().save(force_insert, only)        

    @classmethod
    def on_livescore_event(cls, data: UpdateData):
        pass

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Game", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        id_event = kwargs.get("id_event")
        query = query.where((cls.id_event == id_event))

        try:
            game: Game = query.get()
            try:
                home_score = kwargs.get("home_score", None)
                away_score = kwargs.get("away_score", None)
                status = kwargs.get("status", None)
                assert game.result
                assert home_score is not None
                assert away_score is not None
                game.home_score = home_score
                game.away_score = away_score
                assert status
                game.status = status
            except AssertionError:
                game,save()
            return game, False
                
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

    @property
    def home_team(self) -> Competitor:
        return next(
            filter(
                lambda t: t.id == self.home_team_id,
                Team(self.home_team_id).team.competitors,
            ),
            None,
        )

    @property
    def away_team(self) -> Competitor:
        return next(
            filter(
                lambda t: t.id == self.away_team_id,
                Team(self.away_team_id).team.competitors,
            ),
            None,
        )
    @property
    def league(self) -> Competition:
        return CompetitionData(self.league_id).competition

    @property
    def Status(self) -> GameStatus:
        return GameStatus(self.status)
    
    @property
    def score(self) -> str:
        return f"{self.home_score}:{self.away_score}"
    
    @property
    def result(self) -> Optional[str]:
        try:
            assert self.home_score > -1
            assert self.away_score > -1
            return f"{self.home_score}:{self.away_score}"
        except AssertionError:
            return None

    @property
    def can_predict(self) -> bool:
        try:
            assert self.start_time < datetime.now(tz=timezone.utc)
            return True
        except AssertionError:
            raise PredictionNotAllow()

    @property
    def canPredict(self) -> bool:
        try:
            return self.can_predict
        except Exception:
            raise False
        
    @property
    def has_started(self) -> bool:
        return self.start_time < datetime.now(tz=timezone.utc)
    
    class Meta:
        database = Database.db
        table_name = "predict_game"

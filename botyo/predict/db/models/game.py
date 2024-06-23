from enum import unique

from psycopg2 import IntegrityError
from botyo.api.footy.item.team import Team
from botyo.predict.db import PredictionNotAllow
from botyo.predict.db.database import Database
from botyo.threesixfive.data import LeagueItem
from botyo.threesixfive.item.competition import CompetitionData
from botyo.threesixfive.item.models import Competition, GameStatus
from .base import DbModel
from peewee import CharField, DateTimeField, IntegerField
from datetime import datetime, timezone

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
                
    @property
    def home_team(self) -> Team:
        return Team(self.home_team_id)
    
    @property
    def away_team(self) -> Team:
        return Team(self.away_team_id)
    
    @property
    def league(self) -> Competition:
        return CompetitionData(self.league_id).competition
    
    @property
    def Status(self) -> GameStatus:
        return GameStatus(self.status)

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

    class Meta:
        database = Database.db
        table_name = "predict_game"

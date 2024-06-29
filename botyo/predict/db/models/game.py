import logging
from typing import Optional
from psycopg2 import IntegrityError
from botyo.threesixfive.item.team import Team
from botyo.predict.db.database import Database
from botyo.threesixfive.item.competition import CompetitionData
from botyo.threesixfive.item.models import (
    Competition,
    Competitor,
    GameStatus,
    Game as DataGame,
)
from .base import DbModel, PredictionNotAllow
from peewee import CharField, DateTimeField, IntegerField
from datetime import datetime, timezone


class DbGame(DbModel):
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

    def update_miss(self):
        try:
            assert not self.result
            home_score = self.game.homeCompetitor.score_int
            away_score = self.game.awayCompetitor.score_int
            status = self.game.shortStatusText
            assert home_score is not None
            assert away_score is not None
            self.home_score = home_score
            self.away_score = away_score
            self.save(only=["home_score", "away_score"])
            assert status
            self.status = status
            self.save(only=["status"])
        except AssertionError:
            pass
        return self

    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        id_event = kwargs.get("id_event")
        query = query.where((cls.id_event == id_event))

        try:
            game = query.get()
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
    def display_status(self):
        return self.game.displayStatus

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
    def game(self) -> Optional[DataGame]:
        try:
            ht = Team(self.home_team_id)
            assert ht
            game = next(filter(lambda g: g.id == self.id_event, ht.team.games), None)
            assert game
            return game
        except AssertionError:
            pass
        try:
            at = Team(self.away_team_id)
            assert at
            game = next(filter(lambda g: g.id == self.id_event, at.team.games), None)
            assert game
            return game
        except AssertionError:
            pass
        return None

    @property
    def can_predict(self) -> bool:
        try:
            assert self.start_time.astimezone(tz=timezone.utc) > datetime.now(
                tz=timezone.utc
            )
            return True
        except AssertionError:
            raise PredictionNotAllow

    @property
    def canPredict(self) -> bool:
        try:
            return self.can_predict
        except PredictionNotAllow:
            return False

    @property
    def started(self) -> bool:
        return self.start_time.astimezone(tz=timezone.utc) < datetime.now(
            tz=timezone.utc
        )

    @property
    def ended(self) -> bool:
        try:
            game = self.game
            assert game
            return game.ended
        except:
            return False

    class Meta:
        database = Database.db
        table_name = "predict_game"

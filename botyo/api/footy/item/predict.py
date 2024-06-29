from argparse import ArgumentParser, ArgumentError
from curses.ascii import US
from functools import reduce
import logging
from typing import Optional
import re

from corestring import split_with_quotes
from pydantic import BaseModel
from botyo.api.footy.item.competitions import Competitions
from botyo.api.footy.item.livescore import Livescore
from botyo.api.footy.item.subscription import (
    PredictionClient,
    Subscription,
    SubscriptionClass,
)
from botyo.predict.db.models import DbUser, DbGame, DbPrediction
from botyo.server.output import TextOutput


class PredictArguments(BaseModel):
    query: Optional[list[str]] = None
    user: Optional[str] = None
    all: Optional[bool] = None

    @property
    def query_str(self) -> str:
        try:
            assert self.query
            return " ".join(self.query)
        except AssertionError:
            return ""


class Predict(object):

    __user: Optional[DbUser] = None
    __parser: Optional[ArgumentParser] = None

    def __init__(self, client: str, source: str):
        self.client = client
        if not source.startswith("+"):
            source = "+" + re.findall(r"^(\d+)", source).pop(0)
        self.source = source
        self.__args = PredictArguments(all=False)

    @property
    def parser(self):
        try:
            assert self.__parser
        except AssertionError:
            parser = ArgumentParser(description="Predict options", exit_on_error=False)
            parser.add_argument("query", nargs="*", help="league search string")
            parser.add_argument("-u", "--user", type=str, help="user to show")
            parser.add_argument(
                "--all", action="store_true", help="show all completed predictions"
            )
            self.__parser = parser
        return self.__parser

    def exec(self, query: str):
        try:
            parser = self.parser
            namespace, _ = parser.parse_known_args(split_with_quotes(query))
            self.__args = PredictArguments(**namespace.__dict__)
            assert self.__args.user
            return self.for_user(self.__args.user)
        except ArgumentError:
            return self.parser.usage()
        except AssertionError:
            return self.predict(self.__args.query_str)

    @property
    def get_predictions(self):
        if self.__args.all:
            return DbPrediction.get_calculated
        return DbPrediction.get_in_progress

    @property
    def user(self) -> DbUser:
        if not self.__user:
            user, _ = DbUser.get_or_create(phone=self.source)
            self.__user = user
        return self.__user

    def getGame(self, **kwds) -> DbGame:
        game, _ = DbGame.get_or_create(**kwds)
        return game

    def today_predictions(self) -> str:
        predictions = [x.prediction_row for x in self.get_predictions(User=self.user)]
        TextOutput.addRows([f"Predictions by {self.user.display_name}", *predictions])
        try:
            assert predictions
            return TextOutput.render()
        except AssertionError:
            TextOutput.clean()
            return f"{self.user.display_name} > No predictions"

    def for_user(self, username: str):
        try:
            user = DbUser.get(DbUser.name == username)
            assert user
            predictions = [x.prediction_row for x in self.get_predictions(User=user)]
            TextOutput.addRows([f"Predictions by {user.display_name}", *predictions])
            assert predictions
            return TextOutput.render()
        except AssertionError:
            TextOutput.clean()
            return f"{username} > No predictions"

    def predict(self, query: Optional[str] = None):
        if not query:
            return self.today_predictions()
        qc, preds = self.process_query(query)
        logging.warning(qc)
        comp = Competitions.search(" ".join(qc))

        assert comp
        ls = Livescore(
            with_details=False,
            with_progress=False,
            leagues=[comp.id],
        )
        games = list(filter(lambda x: x.hasNotStarted, ls.items))
        try:
            assert len(games)
        except AssertionError:
            return "No games to predict"
        try:
            assert len(preds) == len(games)
        except AssertionError:
            return ls.render(group_by_league=False, not_started=True)
        predictions = []
        for pred, game in zip(preds, sorted(games, key=lambda x: x.sort)):
            pred_game = self.getGame(
                id_event=game.idEvent,
                league_id=game.idLeague,
                home_team_id=game.idHomeTeam,
                away_team_id=game.idAwayTeam,
                status=game.strStatus,
                start_time=game.startTime,
                home_score=game.intHomeScore,
                away_score=game.intAwayScore,
            )
            sc = PredictionClient(
                client_id=SubscriptionClass.PREDICTION.value,
                group_id="on_livescore_event",
            )
            sub = Subscription.get(event=game, sc=sc)
            sub.schedule(sc)
            pred_pred, is_created = DbPrediction.get_or_create(
                User=self.user, Game=pred_game, prediction=pred
            )
            if not is_created:
                pred_pred.prediction = pred
                pred_pred.save(only=["prediction"])
            predictions.append(pred_pred.prediction_row)

        TextOutput.addRows([f"Predictions by {self.user.display_name}", *predictions])
        return TextOutput.render() if len(predictions) else None

    def process_query(self, query: str) -> tuple[list[str]]:
        patt = re.compile(r"^\d+[^\d]\d+")

        def reduce_func(r: tuple, q: str):
            if patt.match(q):
                r[1].append(q)
            else:
                r[0].append(q)
            return r

        return tuple(reduce(reduce_func, query.split(), ([], [])))

from curses.ascii import US
from functools import reduce
import logging
from typing import Optional
import re
from botyo.api.footy.item.competitions import Competitions
from botyo.api.footy.item.livescore import Livescore
from botyo.api.footy.item.subscription import Subscription, SubscriptionClass, SubscriptionClient
from botyo.predict.db.models import DbUser, DbGame, DbPrediction
from botyo.server.output import TextOutput


class Predict(object):

    __user: Optional[DbUser] = None

    def __init__(self, client: str, source: str):
        self.client = client
        if not source.startswith("+"):
            source = "+" + re.findall(r"^(\d+)", source).pop(0)
        self.source = source

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
        predictions = [
            x.prediction_row for x in DbPrediction.get_in_progress(User=self.user)
        ]
        predictions.insert(0, f"Predictions by {self.user.display_name}")
        TextOutput.addRows(predictions)
        return TextOutput.render() if len(predictions) else None

    def predict(self, query: Optional[str] = None):
        if not query:
            return self.today_predictions()
        qc, preds = self.process_query(query)
        comp = Competitions.search(" ".join(qc))
        assert comp
        ls = Livescore(
            with_details=False,
            with_progress=False,
            leagues=[comp.id],
            inprogress=False,
        )
        games = ls.items
        try:
            assert len(preds) == len(games)
        except AssertionError:
            return ls.render(group_by_league=False)
        predictions = [f"Predictions by {self.user.display_name}"]
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
            sc = SubscriptionClient(
                client_id=SubscriptionClass.PREDICTION.value, group_id="on_livescore_event"
            )
            _ = Subscription.get(event=game, sc=sc)
            pred_pred, is_created = DbPrediction.get_or_create(
                User=self.user, Game=pred_game, prediction=pred
            )
            if not is_created:
                pred_pred.prediction = pred
                pred_pred.save(only=["prediction"])
            predictions.append(pred_pred.prediction_row)

        TextOutput.addRows(predictions)
        return TextOutput.render() if len(predictions) else None

    def process_query(self, query: str) -> tuple[list[str]]:

        def reduce_func(r: tuple, q: str):
            if q[0].isdigit():
                r[1].append(q)
            else:
                r[0].append(q)
            return r

        return tuple(reduce(reduce_func, query.split(), ([], [])))

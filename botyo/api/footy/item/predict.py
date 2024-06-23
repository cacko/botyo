from curses.ascii import US
from functools import reduce
import logging
from typing import Optional

from botyo.api.footy.item.competitions import Competitions
from botyo.api.footy.item.components import ScoreRow
from botyo.api.footy.item.livescore import Livescore
from botyo.api.footy.item.subscription import Subscription, SubscriptionClient
from botyo.predict.db.models import User, Game, Prediction
from botyo.server.output import TextOutput


class Predict(object):

    __user: Optional[User] = None

    def __init__(self, client: str, source: str):
        self.client = client
        self.source = source
        logging.warn(f"predict client = {source}")

    @property
    def user(self) -> User:
        if not self.__user:
            user, _ = User.get_or_create(phone=self.source)
            self.__user = user
        return self.__user

    def getGame(self, **kwds) -> Game:
        game, _ = Game.get_or_create(**kwds)
        return game

    def today_predictions(self) -> str:
        predictions = [x.score_row for x in Prediction.get_in_progress(User=self.user)]
        predictions.insert(0, [f"Predictions by {self.user.display_name}"])
        TextOutput.addRows(predictions)
        return TextOutput.render() if len(predictions) else None

    def predict(self, query: Optional[str] = None):
        if not query:
            return self.today_predictions()
        qc, preds = self.process_query(query)
        comp = Competitions.search(" ".join(qc))
        assert comp
        logging.warn(comp)
        ls = Livescore(
            with_details=False,
            with_progress=False,
            leagues=[comp.id],
            inprogress=False,
        )
        games = ls.items
        assert len(preds) == len(games)
        predictions = [[f"Predictions by {self.user.display_name}"]]
        for pred, game in zip(preds, games):
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
                client_id=self.client,
                group_id="on_livescore_event"
            )
            sub = Subscription.get(
                event=game,
                sc=sc
            )
            logging.warn(sub)
            pred_pred, _ = Prediction.get_or_create(
                User=self.user, Game=pred_game, prediction=pred
            )
            assert pred_pred
            predictions.append(
                ScoreRow(
                    status=game.displayStatus,
                    home=game.strHomeTeam,
                    score=pred,
                    away=game.strAwayTeam,
                    win=game.win,
                    league=game.strLeague,
                    is_international=game.is_international,
                )
            )

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



from functools import reduce
import logging

from torch import Use
from botyo.api.footy.item.competitions import Competitions
from botyo.api.footy.item.components import ScoreRow
from botyo.api.footy.item.livescore import Livescore
from botyo.predict.db.models import User, Game, Prediction
from botyo.server.output import TextOutput


class Predict(object):
    
    def __init__(self, client: str):
        self.client =  client
        logging.warn(f"predict client = {client}")
                
    def predict(self, query: str):
        qc, preds = self.process_query(query)
        comp = Competitions.search(" ".join(qc))
        assert comp
        logging.warn(comp)
        ls =  Livescore (
            with_details=False,
            with_progress=False,
            leagues=[comp.id],
            inprogress=False,
        )
        games = ls.items
        assert len(preds) == len(games)
        user, _ = User.get_or_create(phone=self.client)
        predictions = []
        for pred, game in zip(preds, games):
            pred_game, _ = Game.get_or_create(
                   id_event=game.idEvent,
                    league_id=game.idLeague,
                    home_team_id=game.idHomeTeam,
                    away_team_id=game.idAwayTeam,
                    status=game.strStatus,
                    start_time=game.startTime,
                    home_score=game.intHomeScore,
                    away_score=game.intAwayScore
            )
            pred_pred, _ = Prediction.get_or_create(
                User=user,
                Game=pred_game,
                prediction=pred
            )
            assert pred_pred
            logging.warn([pred_pred, pred_game, pred_pred.can_predict])
            predictions.append(ScoreRow(
                status=game.displayStatus,
                home=game.strHomeTeam,
                score=pred,
                away=game.strAwayTeam,
                win=game.win,
                league=game.strLeague,
                is_international=game.is_international
            ))
        TextOutput.addRows(predictions)
        return (
            TextOutput.render()
            if len(predictions)
            else None
        )
        
    def process_query(self, query: str) -> tuple[list[str]]:
        
        def reduce_func(r:tuple, q:str):
            if q[0].isdigit():
                r[1].append(q)
            else:
                r[0].append(q)
            return r
        
        return tuple(reduce(reduce_func, query.split(), ([], [])))
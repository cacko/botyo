

from functools import reduce
import logging
from botyo.api.footy.item.competitions import Competitions
from botyo.api.footy.item.components import ScoreRow
from botyo.api.footy.item.livescore import Livescore
from botyo.server.output import TextOutput


class Predict(object):
    
    def __init__(self, client: str):
        self.client =  client
        logging.debug(f"predict client = {client}")
                
    def predict(self, query: str):
        qc, preds = self.process_query(query)
        comp = Competitions.search(" ".join(qc))
        assert comp
        logging.debug(comp)
        ls =  Livescore (
            with_details=False,
            with_progress=False,
            leagues=[comp.id],
            inprogress=False,
        )
        games = ls.items
        logging.debug([ls.items, preds])
        assert len(preds) == len(games)
        predictions = []
        for pred, game in zip(preds, games):
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
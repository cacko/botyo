from .livescore_details import ParserDetails
from .models import Event, GameCompetitor
from typing import Optional
from pydantic import BaseModel


class TeamStats(BaseModel):
    home: GameCompetitor
    away: GameCompetitor


class Stats:

    __item: Event

    def __init__(self, item: Event):
        self.__item = item

    @property
    def stats(self) -> Optional[TeamStats]:
        details = ParserDetails.get(self.__item.details)
        if not details:
            return None
        home = details.home
        away = details.away
        assert home
        assert away
        home_stats = home.statistics
        away_stats = away.statistics
        if any([not home_stats, not away_stats]):
            return None
        return TeamStats(
            home=home,
            away=away,
        )

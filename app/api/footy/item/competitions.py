from datetime import datetime, timezone, timedelta

from botyo_server.output import TextOutput, Column, Align
from app.threesixfive.data import Data365
from app.threesixfive.item.models import LeagueItem
from app.threesixfive.item.competition import CompetitionData
from cachable import TimeCacheable
from zoneinfo import ZoneInfo
from itertools import groupby
from app.core.country import Country

class CompetitionItem(TimeCacheable):
    __data: CompetitionData

    def __init__(self, data: CompetitionData):
        self.__data = data

    @property
    def data(self) -> CompetitionData:
        d = self.__data
        return CompetitionData(d.id)

    def render(
            self, tz: ZoneInfo = ZoneInfo("Europe/London")
    ) -> str:
        data =  self.data
        if not data:
            return ""
        games =  data.games
        today = datetime.now(tz=timezone.utc)
        threshold = timedelta(days=1)
        games = sorted(filter(lambda x: today - x.startTime < threshold , games), key=lambda x: x.startTime)
        for d, gms in groupby(games, lambda x: x.startTime.date()):

            rows = [
                [g.displayStatus,
                 g.displayTitle]
                for g in gms
            ]
            rows.append(["", '-' * 36])
            rounds = ','.join(
                list(filter(lambda x: len(x.strip()) > 0, [f"{g.roundName} {g.roundNum}" for g in gms])))
            cols = [
                Column(size=6, align=Align.RIGHT,
                       title=d.strftime("%a").upper()),
                Column(size=36, align=Align.LEFT,
                       title=f'{d.strftime("%b %d %Y").upper()} {rounds}')
            ]

            TextOutput.addColumns(cols, rows, with_header=True)
        return TextOutput.render()


class Competitions:

    leagues: list[int] = []

    def __init__(self, leagues: list[int]):
        self.leagues = leagues

    @property
    def competitions(self) -> list[LeagueItem]:
        return  Data365.leagues

    @property
    def current(self) -> list[LeagueItem]:
        all =  self.competitions
        return list(filter(lambda x: x.id in self.leagues, all))

    def message(self, query: str = "") -> str:
        comps =  self.current
        comps = sorted(
            comps, key=lambda x: f"{x.country_name} {x.league_name}")
        TextOutput.addRows([
            f"{c.country_name.upper()} {c.league_name} ({c.league_id})"
            for c in comps
        ])
        return TextOutput.render()

from datetime import datetime, timezone, timedelta
from botyo.core.config import Config

from botyo.server.output import TextOutput, Column, Align
from botyo.threesixfive.data import Data365
from botyo.threesixfive.data import LeagueItem
from botyo.threesixfive.exception import CompetitionNotFound
from botyo.threesixfive.item.competition import CompetitionData
from cachable import TimeCacheable
from zoneinfo import ZoneInfo
from itertools import groupby
from fuzzelinho import Match, MatchMethod, Needle



class CompetitionNeedle(Needle):
    league_name: str


class CompetitionMatch(Match):
    minRatio = 70
    method = MatchMethod.WRATIO



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
        data = self.data
        if not data:
            return ""
        games = data.games
        today = datetime.now(tz=timezone.utc)
        threshold = timedelta(days=1)
        assert games
        games = sorted(filter(lambda x: today - x.startTime <
                       threshold, games), key=lambda x: x.startTime)
        for d, gms in groupby(games, lambda x: x.startTime.date()):

            rows = [
                [g.displayStatus,
                 f" {g.displayTitle}"]
                for g in gms
            ]
            rows.append(["", '-' * 36])
            rounds = ','.join(
                list(
                    filter(
                        lambda x: len(x) > 0,
                        [f"{g.roundName} {g.roundNum}" for g in gms]
                    )
                )
            )
            cols = [
                Column(size=6, align=Align.RIGHT,
                       title=d.strftime("%a").upper()),
                Column(size=36, align=Align.LEFT,
                       title=f' {d.strftime("%b %d %Y").upper()} {rounds}')
            ]

            TextOutput.addColumns(cols, rows, with_header=True)
        return TextOutput.render()


class CompetitionsMeta(type):
    
    __instances: dict[str, 'Competitions'] = {}
    
    def __call__(cls, *args, **kwargs):
        k = cls.__name__
        if k not in cls.__instances:
            cls.__instances[k] = type.__call__(cls, *args, **kwargs)
        return cls.__instances[k]

    def search(cls, query: str):
        if not query.strip():
            raise CompetitionNotFound
        items = cls().current
        try:
            idCompetition = int(query)
            res = next(filter(lambda x: x.id == idCompetition, items), None)
            if not res:
                raise CompetitionNotFound
            return res
        except ValueError:
            pass
        matcher = CompetitionMatch(haystack=items)
        results = matcher.fuzzy(
            CompetitionNeedle(
                league_name=query,
            )
        )
        if not len(results):
            raise CompetitionNotFound
        return results[0]

class Competitions(object, metaclass=CompetitionsMeta):

    leagues: list[int] = []

    def __init__(self):
        self.leagues = Config.ontv.leagues

    @property
    def competitions(self) -> list[LeagueItem]:
        return Data365.leagues

    @property
    def current(self) -> list[LeagueItem]:
        all = self.competitions
        return list(filter(lambda x: x.id in self.leagues, all))

    def message(self, query: str = "") -> str:
        comps = self.current
        comps = sorted(
            comps, key=lambda x: f"{x.country_name} {x.league_name}")
        TextOutput.addRows([
            f"{c.country_name.upper()} {c.league_name} ({c.league_id})"
            for c in comps
        ])
        return TextOutput.render()

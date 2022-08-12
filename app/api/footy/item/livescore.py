from .components import ScoreFormat, ScoreRow
from .livescore_details import ParserDetails
from app.threesixfive.exception import GameNotFound
from botyo_server.output import TextOutput
from app.threesixfive.item.livescore import Livescore as LivescoreData
from datetime import datetime, timezone, timedelta
from .subscription import Cache
from .player import Player
from fuzzelinho import Match, MatchMethod
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Optional
from itertools import chain
from functools import reduce


class GameMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class GameNeedle:
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""
    strLeague: Optional[str] = ""


def to_groups(res, row: ScoreRow):
    if not len(res):
        return [(row.league, [row])]
    leagues = [l for l, _ in res]
    try:
        idx = leagues.index(row.league)
        res[idx][1].append(row)
        return res
    except ValueError:
        res.append((row.league, [row]))
        return res


class Livescore(LivescoreData):

    def __init__(self, with_progress=False, leagues: list[int] = ..., with_details=False, inprogress=False):
        super().__init__(with_progress, leagues, with_details, inprogress)

    def precache(self):
        now = datetime.now(tz=timezone.utc)
        timeframe = timedelta(minutes=120)
        items = filter(
            lambda ev: (ev.startTime - now) < timeframe,
            self.items
        )
        for ev in items:
            cache = Cache(ev.details)
            content =  cache.content
            if not content:
                continue
            game = content.game
            if game is not None:
                Player.store(game)

    def render(self, filt: str = "", group_by_league=True):
        items =  self.items

        if self.inprogress:
            items = list(filter(lambda x: x.inProgress, items))
        items.reverse()
        filteredIds = [
            x.id for x in
            GameMatch(haystack=items).fuzzy(GameNeedle(
                strHomeTeam=filt,
                strAwayTeam=filt,
                strLeague=filt
            ))
        ] if filt else []
        filtered: list[ScoreRow] = [
            ScoreRow(
                status=x.displayStatus,
                home=x.strHomeTeam,
                score=x.displayScore,
                away=x.strAwayTeam,
                win=x.strWinDescription if x.displayStatus == "AET" else "",
                league=x.strLeague
            )
            for x in sorted(items, key=lambda itm: itm.sort)
            if any(
                [
                    not filt,
                    x.id in filteredIds,
                ]
            )
        ]
        if len(filtered) == 1:
            x = filtered[0]
            x.format = ScoreFormat.STANDALONE
            itm = next(
                filter(
                    lambda y: y.strHomeTeam == x.home
                    and y.strAwayTeam == x.away,
                    items
                ),
                None,
            )
            try:
                details =  ParserDetails.get(itm.details)
                if details:
                    TextOutput.addRows([
                        x,
                        *map(str, details.rendered)
                    ])
                    return TextOutput.render()
            except GameNotFound:
                return None
        if group_by_league:
            filtered = list(chain.from_iterable([
                [l.upper(), *g]
                for l, g in reduce(to_groups, filtered, [])]))

        TextOutput.addRows(filtered)
        return (
            TextOutput.render()
            if len(filtered)
            else None
        )

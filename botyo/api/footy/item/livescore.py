from .components import ScoreFormat, ScoreRow
from .livescore_details import ParserDetails
from botyo.threesixfive.exception import GameNotFound
from botyo.server.output import TextOutput
from botyo.threesixfive.item.livescore import Livescore as LivescoreData
from datetime import datetime, timezone, timedelta
from .subscription import Cache
from .player import Player
from fuzzelinho import Match, MatchMethod, Needle
from typing import Optional
from itertools import chain
from functools import reduce
import logging


class GameMatch(Match):
    minRatio = 70
    method = MatchMethod.WRATIO


class GameNeedle(Needle):
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""
    strLeague: Optional[str] = ""


def to_groups(res, row: ScoreRow):
    if not len(res):
        return [(row.league, [row])]
    leagues = [lg for lg, _ in res]
    try:
        idx = leagues.index(row.league)
        res[idx][1].append(row)
        return res
    except ValueError:
        res.append((row.league, [row]))
        return res


class Livescore(LivescoreData):

    def __init__(
            self,
            with_progress=False,
            leagues:
            list[int] = [],
            with_details=False,
            inprogress=False,
            notEnded=False
    ):
        self.not_ended = notEnded
        super().__init__(with_progress, leagues, with_details, inprogress)

    def precache(self):
        now = datetime.now(tz=timezone.utc)
        timeframe = timedelta(minutes=120)
        items = filter(
            lambda ev: (ev.startTime - now) < timeframe,
            self.items
        )
        if self.not_ended:
            items = filter(
                lambda ev: not ev.hasEnded,
                self.items
            )
        for ev in items:
            try:
                assert ev
                assert ev.details
                cache = Cache(ev.details)
                content = cache.content
                if not content:
                    continue
                game = content.game
                if game is not None:
                    Player.store(game)
            except AssertionError as e:
                logging.exception(e)
                pass

    def render(self, filt: str = "", group_by_league=True):
        items = self.items
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
        logging.debug(f"filtered {filteredIds}")
        filtered: list[ScoreRow] = [
            ScoreRow(
                status=x.displayStatus,
                home=x.strHomeTeam,
                score=x.displayScore,
                away=x.strAwayTeam,
                win=x.win,
                league=x.strLeague,
                is_international=x.is_international
            )
            for x in sorted(items, key=lambda itm: itm.sort)
            if any(
                [
                    not filt,
                    x.id in filteredIds,
                ]
            )
        ]
        logging.debug(f"filtered {filtered}")
        if len(filtered) == 1:
            x = filtered[0]
            x.format = ScoreFormat.STANDALONE
            itm = next(
                filter(
                    lambda y: all([
                        y.strHomeTeam == x.row.home,
                        y.strAwayTeam == x.row.away
                    ]),
                    items
                ),
                None,
            )
            try:
                assert itm
                details = ParserDetails.get(itm.details)
                if details:
                    TextOutput.addRows([
                        x,
                        *map(str, details.rendered)
                    ])
                    return TextOutput.render()
            except (GameNotFound, AssertionError) as e:
                logging.exception(e)
                return None
        if group_by_league:
            filtered = list(
                chain.from_iterable([  # type: ignore
                    [lg.upper(), *g]  # type: ignore
                    for lg, g in reduce(to_groups, filtered, [])
                ]))

        TextOutput.addRows(filtered)
        return (
            TextOutput.render()
            if len(filtered)
            else None
        )

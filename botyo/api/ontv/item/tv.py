from math import floor
from zoneinfo import ZoneInfo
from cachable.request import Request
from datetime import datetime, timedelta, timezone
from botyo.server.output import TextOutput, Align, Column, shorten
from coretime import time_hhmm
from functools import reduce
from pydantic import BaseModel
import json


class Event(BaseModel):
    id: str
    event_id: int
    name: str
    time: datetime
    channels: list[str]
    # tvchannels: list[int]
    sport: str
    country: str
    season: str
    home_team: str = ""
    away_team: str = ""
    league_id: int = 0
    league_name: str = ""
    has_expired: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        self.has_expired = (
            datetime.now(tz=timezone.utc) - timedelta(hours=3) > self.time
        )

    def shortenEventName(self, size=36, joiner=" vs "):
        max_team_size = floor((size - len(joiner)) / 2)
        ht = shorten(
            self.home_team, max_team_size, extraSize=max_team_size - len(self.away_team)
        )
        at = shorten(
            self.away_team, max_team_size, extraSize=max_team_size - len(self.home_team)
        )
        return joiner.join([ht, at])


def to_groups(res, ev: Event):
    if not len(res):
        return [(ev.league_name, [ev])]
    leagues = [l for l, _ in res]
    try:
        idx = leagues.index(ev.league_name)
        res[idx][1].append(ev)
        return res
    except ValueError:
        res.append((ev.league_name, [ev]))
        return res


class TV:

    __request: Request
    LEAGUES: list[int] = []

    def __init__(self, request: Request, leagues: list[int] = []):
        self.__request = request
        self.LEAGUES = leagues

    @property
    def events(self) -> list[Event]:
        body = self.__request.body
        events= [Event(**x) for x in json.loads(body)]
        return filter(
            lambda x: all([not x.has_expired, x.league_id in self.LEAGUES]), events
        )

    def render(
        self,
        filt: str = "",
        group_by_league=True,
        tz: ZoneInfo = ZoneInfo("Europe/Sofia"),
    ) -> str:
        events = list(
            filter(
                lambda ev: any(
                    [
                        not len(filt),
                        filt.lower() in ev.name.lower(),
                        filt.lower() in ev.league_name.lower(),
                    ]
                ),
                self.events,
            )
        )
        if not events:
            return None
        elif len(events) == 1:
            ev = events[0]
            TextOutput.clean()
            TextOutput.addColumns(
                (Column(size=5, align=Align.RIGHT), Column(align=Align.LEFT, size=37)),
                [
                    ("event:", ev.shortenEventName()),
                    ("time:", f"{time_hhmm(ev.time, tz)} {tz}"),
                    ("league:", ev.league_name),
                    ("tv:", ev.channels[0].upper()),
                    *[("", c.upper()) for c in ev.channels[1:]],
                ],
            )
        else:
            TextOutput.clean()
            columns = (
                Column(size=6, align=Align.CENTER),
                Column(size=36, align=Align.LEFT),
            )
            for l, g in reduce(to_groups, events, []):
                TextOutput.addRows([l.upper()])
                TextOutput.addColumns(
                    columns,
                    [[time_hhmm(ev.time, tz), ev.shortenEventName()] for ev in g],
                )
        return TextOutput.render()

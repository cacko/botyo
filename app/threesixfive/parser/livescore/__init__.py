from app.threesixfive.item.models import Event
from prokopiy import Progress
from .parser import Parser, ParserResponse
from hashlib import md5


class Livescores:

    with_progress = False
    with_details = False
    leagues = []

    def __init__(
        self,
        with_progress=False,
        leagues: list[int] = [],
        with_details=False
    ):
        self.with_progress = with_progress
        self.leagues = leagues
        self.with_details = with_details

    def fetch(self) -> list[Event]:
        parser = Parser(with_details=self.with_details, leagues=self.leagues)
        parser.fetch()
        result: list[Event] = []
        sports = {e.id: e for e in parser.sports}
        with Progress() as progress:
            for ev in progress.track(parser.events):
                result.append(
                    Event(
                        strSport=sports.get(ev.sportId).name,
                        idLeague=ev.league_id,
                        strLeague=ev.league,
                        idHomeTeam=ev.team1Id,
                        idAwayTeam=ev.team2Id,
                        strHomeTeam=ev.team1,
                        strAwayTeam=ev.team2,
                        strStatus=ev.status,
                        startTime=ev.startTime,
                        intHomeScore=ev.team1Score if ev.status != "PPD" else -1,
                        intAwayScore=ev.team2Score if ev.status != "PPD" else -1,
                        sort=0,
                        details=ev.details,
                        strWinDescription=ev.winDescription,
                        **self.__getIds(ev),
                    )
                )
        return result

    def __getIds(self, ev: ParserResponse) -> dict[str:any]:
        keys = ("id", "idEvent")
        values = (md5(f"{ev.team1}/{ev.team2}".lower().encode()).hexdigest(), ev.id)
        return dict(zip(keys, values))

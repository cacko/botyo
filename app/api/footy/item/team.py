from zoneinfo import ZoneInfo
from botyo_server.output import TextOutput, Align, Column
from coretime import time_hhmm
from app.threesixfive.item.models import Competitor
from app.threesixfive.item.team import Team as DataTeam, TeamStruct


class Team:
    __competitor: Competitor = None

    def __init__(self, competitor: Competitor):
        self.__competitor = competitor

    @property
    def data(self) -> TeamStruct:
        t = DataTeam(self.__competitor.id)
        res =  t.team
        return res

    def render(
            self, tz: ZoneInfo = ZoneInfo("Europe/London")
    ) -> str:
        team =  self.data
        if not team:
            return ""

        TextOutput.clean()
        columns = [
            Column(size=25, align=Align.RIGHT, title="vs"),
            Column(align=Align.LEFT, size=25, title="league"),
            Column(align=Align.LEFT, size=25, title="time"),
            Column(align=Align.LEFT, size=25, title="info")
        ]
        rows = []
        for game in team.games:
            g = []
            if game.homeCompetitor.id == self.__competitor.id:
                g.append(game.awayCompetitor.name)
            else:
                g.append(f"@{game.homeCompetitor.name}")

            g.append(game.competitionDisplayName)
            startTime = game.startTime
            g.append(
                f"{startTime.strftime('%a %b %d')} " +
                f"{time_hhmm(startTime, tz)} {tz}"
            )

            if game.not_started or game.canceled or game.postponed:
                g.append(game.statusText)
            else:
                home = game.homeCompetitor
                away = game.awayCompetitor
                g.append(" ".join(filter(None, [
                    f"{home.score:.0f}:{away.score:.0f}",
                    game.winDescription,
                    game.aggregateText
                ])))
            rows.append(g)
        TextOutput.addRobustTable(columns, rows)
        return TextOutput.render()

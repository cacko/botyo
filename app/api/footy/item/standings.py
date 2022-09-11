from botyo_server.output import Align, Column, TextOutput
from app.threesixfive.item.standings import Standings as StandingsData
from app.threesixfive.item.models import Standing
from itertools import groupby


class Standings(StandingsData):
    @property
    def columns(self):
        return (
            Column(size=2, align=Align.LEFT, title="#"),
            Column(size=18, align=Align.LEFT, title="Team"),
            Column(size=2, align=Align.RIGHT, title="PT"),
            Column(size=2, align=Align.RIGHT, title="PL"),
            Column(size=3, align=Align.RIGHT, title="GD"),
        )

    def render(self) -> str:
        data: Standing = self.standing(True)
        if data.groups:
            data.rows.sort(key=lambda x: x.groupNum)
            for k, rows in groupby(data.rows, key=lambda x: x.groupNum):
                group = next(filter(lambda g: g.num == k, data.groups), None)
                self.__renderGroup(list(rows), group.name)
        else:
            self.__renderGroup(data.rows)
        return TextOutput.render()

    def __renderGroup(self, standing_rows, name=None):
        rows = []
        for row in sorted(standing_rows, key=lambda x: x.position):
            gd = int(row.forward - row.against)
            rows.append(
                [
                    f"{row.position:.0f}",
                    row.competitor.name,
                    f"{row.points:.0f}",
                    f"{row.gamePlayed:.0f}",
                    f"{gd:+d}",
                ]
            )
        TextOutput.addTable(self.columns, rows)

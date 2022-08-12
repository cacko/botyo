from botyo_server.output import Align, Column, TextOutput
from app.threesixfive.item.standings import (
    Standings as StandingsData
)
from app.threesixfive.item.models import Standing


class Standings(StandingsData):

    def render(self) -> str:
        data: Standing =  self.standing(True)
        cols = (
            Column(size=2, align=Align.LEFT, title="#"),
            Column(size=18, align=Align.LEFT, title="Team"),
            Column(size=2, align=Align.RIGHT, title="PT"),
            Column(size=2, align=Align.RIGHT, title="PL"),
            Column(size=3, align=Align.RIGHT, title="GD"),
        )

        rows = []

        for row in sorted(data.rows, key=lambda x: x.position):
            if row.groupNum and row.groupNum > 1:
                continue
            gd = int(row.forward - row.against)
            rows.append([
                f"{row.position:.0f}",
                row.competitor.name,
                f"{row.points:.0f}",
                f"{row.gamePlayed:.0f}",
                f"{gd:+d}",

            ])

        TextOutput.addTable(cols, rows)

        return TextOutput.render()

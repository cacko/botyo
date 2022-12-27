from itertools import groupby
from botyo.core.country import Country
from botyo.server.output import Align, Column, TextOutput
import logging
from botyo.threesixfive.item.models import Standing
from botyo.threesixfive.item.standings import Standings as StandingsData


class Standings(StandingsData):
    def columns(self, group_name=None):
        return (
            Column(size=2, align=Align.LEFT, title="#"),
            Column(
                size=18,
                align=Align.LEFT,
                title="Team" if not group_name else group_name,
            ),
            Column(size=2, align=Align.RIGHT, title="PT"),
            Column(size=2, align=Align.RIGHT, title="PL"),
            Column(size=3, align=Align.RIGHT, title="GD"),
        )

    def render(self, group_query=None) -> str:
        data: Standing = self.standing(True)
        if data.groups and data.rows:
            data.rows = list(filter(lambda x: x.groupNum is not None, data.rows))
            data.rows.sort(key=lambda x: x.groupNum if x.groupNum else -1)
            for k, rows in groupby(data.rows, key=lambda x: x.groupNum):
                group = next(filter(lambda g: g.num == k, data.groups), None)
                if not group:
                    continue
                if (
                    not group_query
                    or group.name.lower().replace("group", "").strip()
                    == group_query.lower()
                ):
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
        logging.warning(row)
        TextOutput.addTable(self.columns(name), rows)

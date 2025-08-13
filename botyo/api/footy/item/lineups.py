from botyo.server.output import Align, Column, TextOutput
from botyo.threesixfive.item.lineups import Lineups as LineupsData
import logging
from typing import Optional
from itertools import product

class Lineups(LineupsData):

    @property
    def message(self) -> Optional[str]:
        lineups = self.lineups
        if not lineups:
            return None
        home = lineups.home
        away = lineups.away
        members = {m.id: m for m in lineups.members}
        try:
            cols = [(
                Column(size=2, align=Align.RIGHT),
                Column(size=25, align=Align.LEFT),
            ), (
                Column(size=25, align=Align.RIGHT),
                Column(size=2, align=Align.LEFT),
            )]
            rows = [
                [
                    f"{members[h.id].jerseyNumber}",
                    f" {members[h.id].name}",
                ],
                [
                    f"{members[a.id].name} ",
                    f"{members[a.id].jerseyNumber}",
                ]
                for h, a in zip(home.lineup, away.lineup)
            ]
            assert home.team.name
            assert away.team.name
            TextOutput.addColumns(
                [Column(size=15, align=Align.LEFT),
                 Column(size=15, align=Align.RIGHT)],
                [[home.team.name.upper(), away.team.name.upper()]],
            )
            for c, r in product(cols, rows):
                TextOutput.addColumns(list(c), r)
            return TextOutput.render()
        except Exception as e:
            logging.exception(e, exc_info=True)
            return None

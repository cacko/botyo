from botyo_server.output import Align, Column, TextOutput
from app.threesixfive.item.lineups import Lineups as LineupsData

class Lineups(LineupsData):

    @property
    def message(self) -> str:
        lineups = self.lineups
        if not lineups:
            return None
        home = lineups.home
        away = lineups.away
        members = {m.id: m for m in lineups.members}
        try:
            cols = (
                Column(size=2, align=Align.RIGHT),
                Column(size=20, align=Align.LEFT),
                Column(size=20, align=Align.RIGHT),
                Column(size=2, align=Align.LEFT),
            )
            rows = [
                (
                    members[h.id].jerseyNumber,
                    members[h.id].name,
                    members[a.id].name,
                    members[a.id].jerseyNumber,
                )
                for h, a in zip(home.lineup, away.lineup)
            ]
            TextOutput.addColumns(
                (Column(size=21, align=Align.LEFT),
                 Column(size=21, align=Align.RIGHT)),
                [(home.team.name.upper(), away.team.name.upper())],
            )
            TextOutput.addColumns(cols, rows)
            return TextOutput.render()
        except Exception as e:
            logging.exception(e, exc_info=True)
            return None

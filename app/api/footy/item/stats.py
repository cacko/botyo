from botyo_server.output import Align, Column, TextOutput
from app.threesixfive.item.stats import Stats as StatsData


class Stats(StatsData):

    @property
    def message(self) -> str:
        stats =  self.stats
        if not stats:
            return None
        home = stats.home
        away = stats.away
        home_stats = home.statistics
        away_stats = away.statistics
        TextOutput.addColumns(
            cols=(
                Column(size=21, align=Align.LEFT),
                Column(size=21, align=Align.RIGHT),
            ),
            content=[(home.name.upper(), away.name.upper())],
        )
        cols = (
            Column(size=10, align=Align.LEFT),
            Column(size=22, align=Align.CENTER),
            Column(size=10, align=Align.RIGHT),
        )
        content = [
            (h_s.value, h_s.name, a_s.value)
            for h_s, a_s in zip(home_stats, away_stats)
        ]

        TextOutput.addColumns(cols, content)

        return TextOutput.render()
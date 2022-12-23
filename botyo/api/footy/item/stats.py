from botyo.server.output import Align, Column, TextOutput
from botyo.threesixfive.item.stats import Stats as StatsData


class Stats(StatsData):
    @property
    def message(self) -> str:
        try:
            stats = self.stats
            if not stats:
                return ""
            home = stats.home
            away = stats.away
            home_stats = home.statistics
            away_stats = away.statistics
            assert home.name
            assert away.name
            TextOutput.addColumns(
                cols=[
                    Column(size=21, align=Align.LEFT),
                    Column(size=21, align=Align.RIGHT),
                ],
                content=[[home.name.upper(), away.name.upper()]],
            )
            cols = [
                Column(size=10, align=Align.LEFT),
                Column(size=22, align=Align.CENTER),
                Column(size=10, align=Align.RIGHT),
            ]
            assert home_stats
            assert away_stats
            content = [
                [h_s.value, h_s.name, a_s.value]
                for h_s, a_s in zip(home_stats, away_stats)
            ]

            TextOutput.addColumns(cols, content)

            return TextOutput.render()
        except AssertionError:
            return ""

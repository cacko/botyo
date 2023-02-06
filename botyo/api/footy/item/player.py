from botyo.server.output import Align, Column, TextOutput

from botyo.threesixfive.item.models import LineupMember
from botyo.threesixfive.item.player import Player as PlayerData


class Player(PlayerData):
    @property
    def message(self) -> str:
        try:
            assert self._struct
            assert self._struct.member.name
            txt = self._struct.member.name.upper()[:45]
            TextOutput.addRows([f"{txt:<45}"])
            lineupMember: LineupMember = self._struct.lineupMember
            if lineupMember.stats:
                columns = [
                    Column(size=20, align=Align.LEFT),
                    Column(size=15, align=Align.RIGHT),
                ]
                stats = [[s.name, s.value] for s in lineupMember.stats]
                TextOutput.addColumns(cols=columns, content=stats)
            else:
                TextOutput.addRows(["No stats yet"])
            return TextOutput.render()
        except AssertionError:
            return ""

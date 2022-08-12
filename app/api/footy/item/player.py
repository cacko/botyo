from app.threesixfive.item.models import (
    LineupMember,
)
from botyo_server.output import Align, Column, TextOutput
from app.threesixfive.item.player import (
    Player as PlayerData
)


class Player(PlayerData):

    @property
    def message(self) -> str:
        TextOutput.addRows([f"{self._struct.member.name.upper()[:40]:<40}"])
        lineupMember: LineupMember = self._struct.lineupMember
        if lineupMember.stats:
            columns = [
                Column(size=20, align=Align.LEFT),
                Column(size=10, align=Align.RIGHT),
            ]
            stats = ((s.name, s.value) for s in lineupMember.stats)
            TextOutput.addColumns(cols=columns, content=stats)
        else:
            TextOutput.addRows(["No stats yet"])
        return TextOutput.render()

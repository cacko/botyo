from app.threesixfive.item.models import Position
from typing import Generator
from app.threesixfive.item.livescore_details import (
    ParserDetails as ParserDetailsData
)


class ParserDetails(ParserDetailsData):

    @property
    def rendered(self) -> Generator[str, None, None]:
        for ev in self.events:
            if ev.position == Position.HOME:
                row = f"{ev.displayTime:<5}{(ev.icon + ' ' + ev.player):<16}"
                yield f"{row:<42}"
            elif ev.position == Position.AWAY:
                row = f"{(ev.player + ' ' + ev.icon):>16}{ev.displayTime:>5}"
                yield f"{row:>42}"
            else:
                row = f"{ev.displayTime:^5}{ev.icon}"
                yield f"{row:^42}"

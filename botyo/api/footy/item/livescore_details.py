from botyo.threesixfive.item.models import Position
from typing import Generator
from botyo.threesixfive.item.livescore_details import (
    ParserDetails as ParserDetailsData
)
import logging


class ParserDetails(ParserDetailsData):

    @property
    def rendered(self) -> Generator[str, None, None]:
        for ev in self.events:
            try:
                if ev.position == Position.HOME:
                    assert ev.player
                    row = f"{ev.displayTime:<5}{' '.join([ev.icon, ev.player]):<16}"
                    yield f"{row:<42}"
                elif ev.position == Position.AWAY:
                    assert ev.player
                    row = f"{' '.join([ev.player, ev.icon]):>16}{ev.displayTime:>5}"
                    yield f"{row:>42}"
                else:
                    row = f"{ev.displayTime:^5}{ev.icon}"
                    yield f"{row:^42}"
            except AssertionError as e:
                logging.exception(e)
                pass

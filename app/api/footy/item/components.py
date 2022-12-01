from botyo_server.output import Align, Column, TextOutput
from collections import namedtuple
from enum import Enum
from app.core.country import Country

ScoreData = namedtuple("ScoreData", "status,home,away,score,win", defaults=["vs", ""])


class ScoreFormat(Enum):
    STANDALONE = 1
    LIST = 2


class LeagueRow:

    __title = ""

    def __init__(self, league: str) -> None:
        self.__title = league

    def __str__(self) -> str:
        sz = 16 + 5 + 5 + 16
        cols = Column(size=sz, align=Align.LEFT)
        TextOutput.addColumns([cols], [["-" * sz], [self.__title.upper()]])
        return TextOutput.render()


class ScoreRow:

    row: ScoreData
    format: ScoreFormat = ScoreFormat.LIST
    league: str = ""

    def __init__(
        self,
        status,
        score,
        home,
        away,
        win: str = "",
        format: ScoreFormat = ScoreFormat.LIST,
        league: str = "",
    ):
        self.format = format
        if not score:
            score = "vs"
        self.league = league
        self.row = ScoreData(status=status, score=score, home=home, away=away, win=win)

    def __str__(self) -> str:
        if self.format == ScoreFormat.STANDALONE:
            cols = (
                Column(size=16, align=Align.LEFT),
                Column(size=5, align=Align.RIGHT),
                Column(size=5, align=Align.CENTER),
                Column(size=16, align=Align.RIGHT),
            )
            row = (
                self.home.upper(),
                self.row.status,
                self.row.score,
                self.away.upper(),
            )
        elif self.format == ScoreFormat.LIST:
            cols = (
                Column(size=5, align=Align.RIGHT),
                Column(size=16, align=Align.RIGHT),
                Column(size=5, align=Align.CENTER),
                Column(size=16, align=Align.LEFT),
            )
            row = (
                self.row.status,
                self.home,
                self.row.score,
                self.away,
            )
        else:
            raise NotImplementedError
        TextOutput.addColumns(list(cols), [list(row)])
        if self.row.win:
            TextOutput.addColumns(
                [Column(size=sum([x.size for x in cols]), align=Align.CENTER)],
                [[self.row.win]],
            )
        return TextOutput.render()

    @property
    def home(self) -> str:
        return f"{Country(name=self.row.home).flag}{self.row.home}"

    @property
    def away(self) -> str:
        return f"{Country(name=self.row.away).flag}{self.row.away}"

    @property
    def status(self):
        return self.row.status

    @property
    def score(self):
        return self.row.status

    @property
    def win(self):
        return self.row.win

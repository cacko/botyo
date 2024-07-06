from typing import Optional
from botyo.server.output import Align, Column, TextOutput
from collections import namedtuple
from enum import Enum
from botyo.core.country import Country as Flag


ScoreData = namedtuple("ScoreData", "status,home,away,score,win", defaults=["vs", ""])

PredictionData = namedtuple(
    "PredictionData", "status,home,away,score,prediction,win,points", defaults=["vs", ""]
)


class ScoreFormat(Enum):
    STANDALONE = 1
    LIST = 2
    HEADLINE = 3


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
        is_international: bool = False,
    ):
        self.format = format
        if not score:
            score = "vs"
        self.league = league
        self.is_international = is_international
        self.row = ScoreData(status=status, score=score, home=home, away=away, win=win)

    def __str__(self) -> str:
        match self.format:
            case ScoreFormat.STANDALONE:
                cols = (
                    Column(size=16, align=Align.LEFT),
                    Column(size=5, align=Align.CENTER),
                    Column(size=5, align=Align.CENTER),
                    Column(size=16, align=Align.RIGHT),
                )
                row = (
                    f"{self.home.upper()}",
                    self.row.status,
                    self.row.score,
                    f"{self.away.upper()}",
                )
            case ScoreFormat.LIST:
                cols = (
                    Column(size=5, align=Align.RIGHT),
                    Column(size=16, align=Align.RIGHT),
                    Column(size=10, align=Align.CENTER),
                    Column(size=16, align=Align.LEFT),
                )
                row = (
                    self.row.status,
                    f" {self.home}",
                    self.row.score,
                    f"{self.away}",
                )
            case ScoreFormat.HEADLINE:
                cols = (
                    Column(size=5, align=Align.LEFT),
                    Column(size=16, align=Align.RIGHT),
                    Column(size=5, align=Align.CENTER),
                    Column(size=16, align=Align.LEFT),
                )
                row = (
                    self.row.status,
                    f"{self.home}",
                    self.row.score,
                    f"{self.away}",
                )

        TextOutput.addColumns(list(cols), [list(row)])
        if self.row.win:
            TextOutput.addColumns(
                [Column(size=sum([x.size for x in cols]), align=Align.CENTER)],
                [[self.row.win]],
            )
        return TextOutput.render()

    @property
    def home(self) -> str:
        if self.is_international:
            return f"{Flag(name=self.row.home).with_flag(self.row.home)}"
        return self.row.home

    @property
    def away(self) -> str:
        if self.is_international:
            return f"{Flag(name=self.row.away).with_flag(self.row.away)}"
        return self.row.away

    @property
    def status(self):
        return self.row.status

    @property
    def score(self):
        return self.row.status

    @property
    def win(self):
        return self.row.win


class PredictionRow(ScoreRow):

    row: PredictionData

    def __init__(
        self,
        status,
        prediction,
        home,
        away,
        points,
        win: str = "",
        score: Optional[str] = None,
        format: ScoreFormat = ScoreFormat.LIST,
        league: str = "",
        is_international: bool = False,
        has_ended: bool = False,
    ):
        self.format = format
        if not score:
            score = "vs"
        self.league = league
        self.is_international = is_international
        self.has_ended = has_ended
        self.row = PredictionData(
            status=status,
            score=score,
            prediction=prediction,
            home=home,
            away=away,
            win=win,
            points=points,
        )

    def __str__(self) -> str:

        cols = [
            Column(size=5, align=Align.RIGHT),
            Column(size=16, align=Align.RIGHT),
            Column(size=5, align=Align.CENTER),
            Column(size=16, align=Align.LEFT),
            Column(size=5, align=Align.CENTER),
            Column(size=3, align=Align.CENTER),
        ]
        row = [
            self.row.status,
            f" {self.home}",
            self.row.score,
            f"{self.away}",
            f"{self.row.prediction}",
            f"{self.row.points}"
        ]

        try:
            assert self.has_ended
            cols.pop(0)
            row.pop(0)
        except AssertionError:
            pass
        
        try:
            assert self.row.score == "vs"
            cols.pop()
            row.pop()
        except AssertionError:
            pass


        TextOutput.addColumns(cols, [row])
        if self.row.win:
            TextOutput.addColumns(
                [Column(size=sum([x.size for x in cols]), align=Align.CENTER)],
                [[self.row.win]],
            )
        return TextOutput.render()

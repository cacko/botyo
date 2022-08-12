from datetime import timezone, datetime, timedelta
from .models import Event
from cachable.cacheable import TimeCacheable
from app.threesixfive.parser.livescore import Livescores as Fetcher


class Livescore(TimeCacheable):

    with_progress = False
    with_details = False
    inprogress = False
    leagues = []
    cachetime: timedelta = timedelta(seconds=10)

    def __init__(
        self,
        with_progress=False,
        leagues: list[int] = [],
        with_details=False,
        inprogress=False

    ):
        self.with_progress = with_progress
        self.leagues = leagues
        self.with_details = with_details
        self.inprogress = inprogress

    @property
    def id(self):
        return datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    @property
    def items(self) -> list[Event]:
        if not self.load():
            fetcher = Fetcher(
                with_details=self.with_details,
                with_progress=self.with_progress,
                leagues=self.leagues
            )
            results = fetcher.fetch()
            self._struct = self.tocache(results)
        events: list[Event] = self._struct.struct
        return events

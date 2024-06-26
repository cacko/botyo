import logging
from typing import Optional
from pydantic import BaseModel
from botyo import cli
from botyo.api.footy.item.h2h import H2H

from botyo.api.footy.item.predict import Predict
from botyo.api.footy.item.predict_standings import PredictStandings
from botyo.server.scheduler import Scheduler
from .item.subscription import Subscription, SubscriptionClient
from fuzzelinho import Match, MatchMethod, Needle
from botyo.threesixfive.data import LeagueItem
from botyo.threesixfive.item.models import Event
from botyo.threesixfive.item.team import TeamSearch
from botyo.threesixfive.item.competition import CompetitionData
from .item.player import Player
from .item.stats import Stats
from .item.livescore import Livescore
from .item.lineups import Lineups
from .item.competitions import Competitions
from .item.facts import Facts
from .item.team import Team
from botyo.threesixfive.exception import GameNotFound, TeamNotFound, CompetitionNotFound
from botyo.core.config import Config
from emoji import emojize
from apscheduler.job import Job


class SubscriptionResult(BaseModel):
    message: str
    sub_id: Optional[str] = None


class Goal:
    pass


class FootyMeta(type):
    _instance: Optional["Footy"] = None
    _app = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def register(cls, app):
        cls._instance = cls()

    def livescore(cls, live=False) -> Livescore:
        return cls().getLivescore(live)

    def lineups(cls, query: str) -> Lineups:
        return cls().getLineups(query)

    def facts(cls, query: str) -> Facts:
        return cls().getFacts(query)

    def team(cls, query: str) -> Team:
        return cls().getTeam(query)

    def goals(cls, query: str) -> list[Goal]:
        return cls().getGoals(query)

    def stats(cls, query: str) -> Stats:
        return cls().getStats(query)

    def h2h(cls, query: str) -> H2H:
        return cls().getH2H(query)

    def player(cls, query: str) -> Player:
        return cls().getPlayer(query)

    def predict(cls, client, source) -> Predict:
        return cls().getPredict(client=client, source=source)

    def predict_standings(cls, client, source) -> PredictStandings:
        return cls().getPredictStandings(client=client, source=source)

    # def precache(cls):
    #     return cls().precacheLivegames()

    def competitions(cls) -> Competitions:
        return cls().getCompetitions()

    def competition(cls, query: str) -> CompetitionData:
        return cls().getCompetition(query)

    def subscribe(cls, client: SubscriptionClient, query: str) -> SubscriptionResult:
        try:
            return cls().getSubscription(query=query, client=client)
        except GameNotFound as e:
            raise e

    def unsubscribe(cls, client, query: str, group) -> SubscriptionResult:
        return cls().removeSubscription(query=query, client=client, group=group)

    def listjobs(cls, client, group) -> list[Job]:
        return Subscription.forGroup(
            SubscriptionClient(client_id=client, group_id=group)
        )


class GameMatch(Match):
    minRatio = 70
    method = MatchMethod.WRATIO


class GameNeedle(Needle):
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""


class Footy(object, metaclass=FootyMeta):
    def __queryGame(self, query) -> Event:
        if not query.strip():
            raise GameNotFound
        items = self.getLivescore().items
        try:
            idEvent = int(query)
            res = next(filter(lambda x: x.idEvent == idEvent, items), None)
            if not res:
                raise GameNotFound
            return res
        except ValueError:
            pass
        matcher = GameMatch(haystack=items)
        game = matcher.fuzzy(GameNeedle(strHomeTeam=query, strAwayTeam=query))
        if not len(game):
            raise GameNotFound
        return game[0]

    def __queryTeam(self, query) -> Team:
        if len(query.strip()) < 4:
            raise TeamNotFound
        search = TeamSearch(query)
        item = search.competitor
        if not item:
            raise TeamNotFound
        return Team(item)

    def __queryCompetition(self, query) -> LeagueItem:
        return Competitions.search(query)

    def getLivescore(self, inprogress=False) -> Livescore:
        return Livescore(
            with_details=False,
            with_progress=False,
            leagues=Config.ontv.leagues,
            inprogress=inprogress,
        )

    def getCompetitions(self) -> Competitions:
        return Competitions()

    def getGoals(self, query: str) -> list[Goal]:
        _ = self.__queryGame(query)
        return []

    def getPredict(self, client: str, source: Optional[str] = None) -> Predict:
        return Predict(client=client, source=source)

    def getPredictStandings(
        self, client: str, source: Optional[str] = None
    ) -> PredictStandings:
        return PredictStandings(client=client, source=source)

    def getCompetition(self, query: str) -> CompetitionData:
        item = self.__queryCompetition(query)
        return CompetitionData(item.id)

    def getTeam(self, query: str) -> Team:
        item = self.__queryTeam(query)
        return item

    def getLineups(self, query: str) -> Lineups:
        item = self.__queryGame(query)
        return Lineups(item)

    def getFacts(self, query: str) -> Facts:
        item = self.__queryGame(query)
        return Facts(item)

    def getStats(self, query: str) -> Stats:
        item = self.__queryGame(query)
        return Stats(item)

    def getH2H(self, query: str) -> H2H:
        item = self.__queryGame(query)
        return H2H(item)

    def getPlayer(self, query: str) -> Player:
        player = Player.find(query)
        return player

    def removeSubscription(
        self, client: SubscriptionClient, query: str
    ) -> SubscriptionResult:
        item = self.__queryGame(query)
        sub = Subscription.get(event=item, sc=client)
        sub_id = sub.id
        sub.cancel(client)
        icon = emojize(":dango:")
        return SubscriptionResult(
            message=f"{icon} {item.strHomeTeam} vs {item.strAwayTeam}", sub_id=sub_id
        )

    def getSubscription(
        self, client: SubscriptionClient, query: str
    ) -> SubscriptionResult:
        try:
            item = self.__queryGame(query)
            sub = Subscription.get(event=item, sc=client)
            if not sub.isValid:
                return SubscriptionResult(message="Event has ended".upper())
            sub.schedule(client)
            return SubscriptionResult(
                message=" ".join(
                    [
                        f"{emojize(':bell:')}",
                        f"{item.strHomeTeam} vs {item.strAwayTeam}",
                    ]
                ),
                sub_id=sub.id,
            )
        except Exception:
            raise GameNotFound

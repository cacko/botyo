import logging
from typing import Optional
from pydantic import BaseModel

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

    def team(cls, query: str) -> Team:
        return cls().getTeam(query)

    def goals(cls, query: str) -> list[Goal]:
        return cls().getGoals(query)

    def stats(cls, query: str) -> Stats:
        return cls().getStats(query)

    def player(cls, query: str) -> Player:
        return cls().getPlayer(query)

    # def precache(cls):
    #     return cls().precacheLivegames()

    def competitions(cls) -> Competitions:
        return cls().getCompetitions()

    def competition(cls, query: str) -> CompetitionData:
        return cls().getCompetition(query)

    def subscribe(cls, client, query: str, groupID) -> SubscriptionResult:
        try:
            return cls().getSubscription(query=query, client=client, group=groupID)
        except GameNotFound as e:
            raise e

    def unsubscribe(cls, client, query: str, group) -> SubscriptionResult:
        return cls().removeSubscription(query=query, client=client, group=group)

    def listjobs(cls, client, group) -> list[Job]:
        return Subscription.forGroup(
            SubscriptionClient(client_id=client, group_id=group)
        )


class GameMatch(Match):
    minRatio = 60
    method = MatchMethod.WRATIO


class GameNeedle(Needle):
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""


class CompetitionNeedle(Needle):
    league_name: str


class CompetitionMatch(Match):
    minRatio = 10
    method = MatchMethod.SIMILARITY


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
        logging.warn(items)
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
        if not query.strip():
            raise CompetitionNotFound
        items = self.getCompetitions().current
        try:
            idCompetition = int(query)
            res = next(filter(lambda x: x.id == idCompetition, items), None)
            if not res:
                raise CompetitionNotFound
            return res
        except ValueError:
            pass
        matcher = CompetitionMatch(haystack=items)
        results = matcher.fuzzy(
            CompetitionNeedle(
                league_name=query,
            )
        )
        if not len(results):
            raise CompetitionNotFound
        return results[0]

    def getLivescore(self, inprogress=False) -> Livescore:
        return Livescore(
            with_details=False,
            with_progress=False,
            leagues=Config.ontv.leagues,
            inprogress=inprogress,
        )

    def getCompetitions(self) -> Competitions:
        return Competitions(
            Config.ontv.leagues,
        )

    def getGoals(self, query: str) -> list[Goal]:
        _ = self.__queryGame(query)
        return []

    def getCompetition(self, query: str) -> CompetitionData:
        item = self.__queryCompetition(query)
        return CompetitionData(item.id)

    def getTeam(self, query: str) -> Team:
        item = self.__queryTeam(query)
        return item

    def getLineups(self, query: str) -> Lineups:
        item = self.__queryGame(query)
        return Lineups(item)

    def getStats(self, query: str) -> Stats:
        item = self.__queryGame(query)
        return Stats(item)

    def getPlayer(self, query: str) -> Player:
        player = Player.find(query)
        return player

    def removeSubscription(self, client: str, query: str, group) -> SubscriptionResult:
        item = self.__queryGame(query)
        sc = SubscriptionClient(client_id=client, group_id=group)
        logging.warning(sc)
        sub = Subscription.get(event=item, sc=sc)
        logging.warning(sub)
        sub_id = sub.id
        sub.cancel(sc)
        logging.warning(sub.id)
        logging.warning(Scheduler.get_jobs())
        icon = emojize(":dango:")
        return SubscriptionResult(
            message=f"{icon} {item.strHomeTeam} vs {item.strAwayTeam}",
            sub_id=sub_id
        )

    def getSubscription(self, client: str, query: str, group) -> SubscriptionResult:
        try:
            item = self.__queryGame(query)
            sc = SubscriptionClient(client_id=client, group_id=group)
            sub = Subscription.get(event=item, sc=sc)
            if not sub.isValid:
                return SubscriptionResult(message="Event has ended".upper())
            sub.schedule(sc)
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

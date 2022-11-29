from typing import Optional
from dataclasses_json import dataclass_json
from dataclasses import dataclass

from .item.subscription import Subscription, SubscriptionClient
from fuzzelinho import Match, MatchMethod
from app.threesixfive.item.models import Event, LeagueItem
from app.threesixfive.item.team import TeamSearch, Team as DataTeam
from app.threesixfive.item.competition import CompetitionData
from .item.player import Player
from .item.stats import Stats
from .item.livescore import Livescore
from .item.facts import Facts
from .item.lineups import Lineups
from .item.competitions import Competitions
from .item.team import Team
from app.threesixfive.exception import GameNotFound, TeamNotFound, CompetitionNotFound
from app.core.config import Config
from emoji import emojize
from apscheduler.job import Job


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

    def player(cls, query: str) -> Player:
        return cls().getPlayer(query)

    # def precache(cls):
    #     return cls().precacheLivegames()

    def competitions(cls) -> Competitions:
        return cls().getCompetitions()

    def competition(cls, query: str) -> CompetitionData:
        return cls().getCompetition(query)

    def subscribe(cls, client, query: str, groupID) -> str:
        try:
            return cls().getSubscription(query=query, client=client, group=groupID)
        except GameNotFound as e:
            raise e

    def unsubscribe(cls, client, query: str, group) -> str:
        return cls().removeSubscription(query=query, client=client, group=group)

    def listjobs(cls, client, group) -> list[Job]:
        return Subscription.forGroup(SubscriptionClient(client_id=client, group_id=group))


class GameMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class GameNeedle:
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""


@dataclass_json
@dataclass
class CompetitionNeedle:
    league_name: str


class CompetitionMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


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
        game = self.__queryGame(query)
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

    def getFacts(self, query: str) -> Facts:
        item = self.__queryGame(query)
        return Facts(item)

    def getStats(self, query: str) -> Stats:
        item = self.__queryGame(query)
        return Stats(item)

    def getPlayer(self, query: str) -> Player:
        player = Player.find(query)
        return player

    def removeSubscription(self, client: str, query: str, group) -> str:
        item = self.__queryGame(query)
        sc = SubscriptionClient(client_id=client, group_id=group)
        sub = Subscription.get(event=item, sc=sc)
        sub.cancel(sc)
        icon = emojize(":dango:")
        return f"{icon} {item.strHomeTeam} vs {item.strAwayTeam}"

    def getSubscription(self, client: str, query: str, group) -> str:
        try:
            item = self.__queryGame(query)
            sc = SubscriptionClient(client_id=client, group_id=group)
            sub = Subscription.get(event=item, sc=sc)
            if not sub.isValid:
                return "Event has ended".upper()
            sub.schedule(sc)
            return f"{emojize(':bell:')} {item.strHomeTeam} vs {item.strAwayTeam}"
        except Exception:
            raise GameNotFound

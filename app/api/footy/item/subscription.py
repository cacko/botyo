from app.api.footy.item.lineups import Lineups
from app.api.logo.team import TeamLogoPixel
from app.threesixfive.exception import GameNotFound
from app.threesixfive.item.league import LeagueImage
from .components import ScoreFormat, ScoreRow
from .livescore_details import ParserDetails
from botyo_server.output import TextOutput
from botyo_server.scheduler import Scheduler
from apscheduler.schedulers.base import JobLookupError
from botyo_server.socket.connection import Connection, UnknownClientException
from botyo_server.models import RenderResult, Attachment
from app.threesixfive.item.models import (
    CancelJobEvent,
    DetailsEventPixel,
    Event,
    GameEvent,
    EventStatus,
    GameStatus,
    ResponseGame,
    SubscriptionEvent,
    GoalEvent,
)
from app.api import ZMethod
from .player import Player
from cachable.request import Request
from cachable.cacheable import Cachable
from enum import Enum
from hashlib import blake2b
from emoji import emojize
from datetime import datetime, timezone
import re
from requests import post
from app.core.otp import OTP
import sys
from pixelme import Pixelate
import time
import logging
from typing import Optional
from .goals import Goals
from app.goals import Query as GoalQuery
from pathlib import Path
from app.core.store import Queue
from dataclasses import dataclass


class Headers(Enum):
    LINEUP_ANNOUNCED = "Lineup Announced"


class JobPrefix(Enum):
    INPROGRESS = "INP"
    SCHEDULED = "SCH"
    BEFOREGAME = "BFG"


class Cache(Cachable):

    _struct: Optional[ResponseGame] = None
    __url: str
    __jobId: str
    __id: Optional[str] = None
    halftime: bool = False

    def __init__(self, url: str, jobId: str = ""):
        self.__url = url
        self.__jobId = jobId

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(f"{self.__jobId}{self.__url}".encode())
            self.__id = h.hexdigest()
        return self.__id

    def fetch(self) -> Optional[ResponseGame]:
        url = f"{self.__url}&{time.time()}"
        req = Request(url)
        try:
            json = req.json
            response: ResponseGame = ResponseGame.from_dict(json)  # type: ignore
            return response
        except Exception as e:
            print(e)
            return None

    @property
    def content(self) -> Optional[ResponseGame]:
        isLoaded = self.load()
        if not isLoaded:
            fetch = self.fetch()
            self._struct = self.tocache(fetch)
        return self._struct

    @property
    def fresh(self) -> ResponseGame:
        fresh = self.fetch()
        self._struct = self.tocache(fresh)
        if not self._struct:
            raise GameNotFound
        return self._struct

    @property
    def update(self) -> Optional[ResponseGame]:
        try:
            cached = self.fromcache()
            if not cached:
                return self.fresh
            fresh = self.fresh
            if cached.status != fresh.status and fresh.status == "HT":
                self.halftime = True
            if len(cached.events) < len(fresh.events):
                content = self.content
                self._struct.game.events = (content).events[len(cached.events) :]  # type: ignore
                return self._struct
            return None
        except GameNotFound:
            return None


@dataclass
class SubscritionClient:
    client_id: str
    group_id: Optional[str] = None

    @property
    def id(self) -> str:
        return __class__.get_id(self.client_id, self.group_id)

    @property
    def is_rest(self) -> bool:
        return self.client_id.startswith("http")

    @classmethod
    def get_id(cls, client: str, group) -> str:
        prefix = ":".join([cls.__module__, client, group])
        h = blake2b(digest_size=20)
        h.update(prefix.encode())
        return h.hexdigest()


class SubscriptionMeta(type):

    __subs: dict[str, "Subscription"] = {}

    def __call__(cls, event: Event):
        k = event.job_id
        if k not in cls.__subs:
            cls.__subs[k] = type.__call__(cls, event)
            cls.clients[k] = []

        return cls.__subs[k]

    def get(cls, event: Event, sc: SubscritionClient) -> "Subscription":
        obj = cls(event)
        k = event.job_id
        if SubscritionClient.id not in [x.id for x in cls.clients[k]]:
            cls.clients[k].append(sc)
        return obj

    def forGroup(cls, sc: SubscritionClient) -> list["Subscription"]:
        subs = list(filter(lambda k: sc.id in cls.clients[k], cls.clients.keys()))
        if not subs:
            return []
        return subs

    @property
    def clients(cls) -> Queue:
        return Queue(f"subscription.clients")


class Subscription(metaclass=SubscriptionMeta):

    _event: Event
    _announceLineups = False

    def __init__(self, event: Event) -> None:
        self._event = event

    @property
    def id(self):
        prefix = JobPrefix.INPROGRESS
        if not self.inProgress:
            prefix = JobPrefix.SCHEDULED
        return ":".join([self._event.job_id, prefix.value])

    @property
    def beforeGameId(self):
        prefix = JobPrefix.BEFOREGAME
        return ":".join([self._event.job_id, prefix.value])

    @property
    def event_name(self):
        return " vs ".join(
            [self._event.strHomeTeam.upper(), self._event.strAwayTeam.upper()]
        )

    @property
    def goals_queue(self) -> Queue:
        return Queue(f"subscription.{self._event.job_id}.goals.queue")

    @property
    def subscriptions(self) -> list[SubscritionClient]:
        return __class__.clients[self._event.job_id]

    def cancel(self, sc: SubscritionClient):
        try:
            if sc.is_rest:
                self.sendUpdate_(CancelJobEvent(job_id=self.id), sc)
                self.subscriptions.remove(sc)
            if not len(self.subscriptions):
                Scheduler.cancel_jobs(self.id)
        except JobLookupError:
            pass

    def cancel_all(self):
        for sc in self.subscriptions:
            self.cancel(sc)

    def sendUpdate(self, message, sc: SubscritionClient):
        if sc.is_rest:
            return self.sendUpdate_(message, sc)
        if not self.client:
            return
        connection = self.client(sc.client_id)
        if not connection:
            raise UnknownClientException
        connection.respond(
            RenderResult(
                method=ZMethod.FOOTY_SUBSCRIBE, message=message, group=sc.group_id
            )
        )

    def sendGoal(self, message: str, attachment: Path):
        for sc in self.subscriptions:
            if sc.is_rest:
                continue
            connection = self.client(sc.client_id)
            if not connection:
                raise UnknownClientException
            connection.respond(
                RenderResult(
                    method=ZMethod.FOOTY_SUBSCRIBE,
                    message=message,
                    attachment=Attachment(
                        path=attachment.as_posix(),
                        contentType="video/mp4",
                    ),
                    group=sc.group_id,
                )
            )

    def processGoals(self, events: list[GameEvent]):
        try:
            assert isinstance(events, list)
            logging.warning(events)
            for x in events:
                if x.is_goal:
                    logging.info(f"GOAL event at {self.event_name}")
                    goal_query = GoalQuery(
                        event_name=self.event_name,
                        event_id=int(self._event.idEvent),
                        game_event_id=x.order_id,
                        title=f"{self._event.strHomeTeam} - {self._event.strAwayTeam} {self._event.displayScore}",
                    )
                    goal_event = GoalEvent(
                        event_id=int(self._event.idEvent),
                        event_name=self.event_name,
                        game_event_id=x.order_id,
                        player=x.playerName,
                        score=self._event.displayScore
                        if self._event.displayScore
                        else "",
                        time=x.displayTime,
                    )
                    Goals.save_metadata(goal_event)
                    Goals.monitor(goal_query)
                    self.goals_queue[goal_query.id] = goal_query
        except AssertionError:
            pass

    def checkGoals(self):
        if not len(self.goals_queue):
            return
        Goals.poll()
        for qid in list(self.goals_queue.keys()):
            gq = self.goals_queue[qid]
            logging.debug(f"CHECK GOALS: {gq}")
            if goal_video := Goals.video(gq):
                self.sendGoal(gq.title, goal_video)
                del self.goals_queue[qid]

    def trigger(self):
        try:
            self.checkGoals()
            assert self._event.details
            cache = Cache(url=self._event.details, jobId=self.id)
            updated = cache.update
            try:
                assert updated
                assert updated.game
                if updated.game.events:
                    self.processGoals(updated.game.events)
            except AssertionError as e:
                logging.debug(e)
                pass
            chatUpdate = self.updates(updated)
            logging.debug(self.subscriptions)
            for sc in self.subscriptions:
                if sc.is_rest:
                    try:
                        details = ParserDetails(None, response=updated)
                        events = details.events_pixel
                        self.sendUpdate_(events, sc)
                    except Exception as e:
                        logging.exception(e)
                    if cache.halftime:
                        cache.halftime = False
                        self.sendUpdate_(self.halftimeAnnoucement_, sc)
                    else:
                        self.sendUpdate_(self.progressUpdate_, sc)
                elif chatUpdate:
                    TextOutput.clean()
                    TextOutput.addRows(chatUpdate)
                    try:
                        self.sendUpdate(TextOutput.render(), sc)
                    except UnknownClientException:
                        pass
            content = cache.content
            if not content:
                return self.cancel_all()
            Player.store(content.game)
            if any(
                [
                    GameStatus(content.game.shortStatusText)
                    in [
                        GameStatus.FT,
                        GameStatus.JE,
                        GameStatus.SUS,
                        GameStatus.ABD,
                        GameStatus.AET,
                        GameStatus.FN,
                    ],
                ]
            ):
                for sc in self.subscriptions:
                    try:
                        if sc.is_rest:
                            self.sendUpdate_(self.fulltimeAnnoucementPixel, sc)
                        else:
                            self.sendUpdate(self.fulltimeAnnoucement, sc)
                    except UnknownClientException:
                        pass
                    self.cancel(sc)
                logging.debug(f"subscription {self.event_name} in done")
        except ValueError as e:
            logging.exception(e)
        except Exception as e:
            logging.exception(e)
            return self.cancel_all()

    def updates(self, updated: Optional[ResponseGame] = None) -> Optional[list[str]]:
        try:
            if not updated:
                return None
            details = ParserDetails(None, response=updated)
            rows = details.rendered
            if not rows:
                return None
            assert details.home
            assert details.away
            res = ScoreRow(
                status=f"{details.game_time:.0f}",
                home=details.home.name,
                away=details.away.name,
                score=details.score,
                format=ScoreFormat.STANDALONE,
                league=self._event.strLeague,
            )
            return [*rows, str(res)]
        except AssertionError:
            return None

    def client(self, client_id: str) -> Optional[Connection]:
        try:
            return Connection.client(client_id)
        except UnknownClientException:
            return None

    @property
    def fulltimeAnnoucement(self):
        logging.info(f"FOOT SUB: Full Time {self.event_name}")
        logging.debug(f"subscription {self.event_name} in done")
        details = ParserDetails.get(str(self._event.details))
        icon = emojize(":chequered_flag:")
        TextOutput.addRows(
            [" ".join([icon, "FULLTIME: ", self.event_name, details.score])]
        )
        return TextOutput.render()

    @property
    def fulltimeAnnoucementPixel(self):
        try:
            details = ParserDetails.get(str(self._event.details))
            return DetailsEventPixel.fullTimeEvent(details=details)
        except AssertionError as e:
            logging.exception(e)

    @property
    def halftimeAnnoucement_(self):
        try:
            details = ParserDetails.get(str(self._event.details))
            return DetailsEventPixel.halfTimeEvent(details)
        except AssertionError as e:
            logging.exception(e)

    @property
    def startAnnouncement(self) -> str | list[str]:
        TextOutput.addRows(
            [" ".join([emojize(":goal_net:"), f"GAME STARTING: {self.event_name}"])]
        )
        return TextOutput.render()

    @property
    def startAnnouncementPixel(self) -> list[DetailsEventPixel]:
        return [DetailsEventPixel.startTimeEvent(self.event_name, self._event.idEvent)]

    def start(self, announceStart=False):
        logging.debug(f"subscriion in live mode {self.event_name}")
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.trigger,
            trigger="interval",
            seconds=60,
            replace_existing=True,
            misfire_grace_time=60,
        )
        if announceStart:
            for sc in self.subscriptions:
                try:
                    if sc.is_rest:
                        self.sendUpdate_(self.startAnnouncementPixel, sc)
                    else:
                        self.sendUpdate(self.startAnnouncement, sc)
                except UnknownClientException:
                    pass

    def schedule(self, sc: SubscritionClient):
        if sc.is_rest:
            logo = LeagueImage(self._event.idLeague)
            logo_path = logo.path
            pix = Pixelate(input=logo_path, padding=200, grid_lines=True, block_size=25)
            pix.resize((8, 8))
            self.sendUpdate_(
                SubscriptionEvent(
                    start_time=self._event.startTime,
                    action="Subscribed",
                    home_team=self._event.strHomeTeam,
                    home_team_id=self._event.idHomeTeam,
                    away_team=self._event.strAwayTeam,
                    away_team_id=self._event.idAwayTeam,
                    event_id=self._event.id,
                    event_name=self.event_name,
                    league=self._event.strLeague,
                    league_id=self._event.idLeague,
                    job_id=self.id,
                    icon=pix.base64,
                    home_team_icon=TeamLogoPixel(self._event.strHomeTeam).base64,
                    away_team_icon=TeamLogoPixel(self._event.strAwayTeam).base64,
                    status=self._event.strStatus,
                ),
                sc,
            )
        if self.inProgress:
            return self.start()
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.start,
            trigger="date",
            replace_existing=True,
            run_date=self._event.startTime,
            kwargs={"announceStart": True},
            misfire_grace_time=180,
        )

    def beforeGameTrigger(self):
        try:
            logging.debug(f"{self.event_name} check for lineups")
            lineups = Lineups(self._event)
            message = lineups.message
            if not message:
                logging.debug(f"{self.event_name} not lineups yet")
                return
            logging.debug(f"{self.event_name} lineups available")
            TextOutput.addRows(
                [f"{Headers.LINEUP_ANNOUNCED.value: ^ 42}\n".upper(), message]
            )
            text = TextOutput.render()
            for sc in filter(lambda s: not s.is_rest, self.subscriptions):
                try:
                    self.sendUpdate(text, sc)
                except UnknownClientException:
                    pass
                self.cancel(sc)
            logging.debug(f"subscription before game {self.event_name} in done")
        except ValueError:
            pass
        except Exception as e:
            logging.error(e)

    @property
    def isValid(self) -> bool:
        return not any([self.isCancelled, self.isPostponed, self.hasEnded])

    @property
    def inProgress(self) -> bool:
        return not any([self.notStarted, self.hasEnded])

    @property
    def isPostponed(self) -> bool:
        try:
            status = EventStatus(self._event.strStatus)
            return status == EventStatus.PPD
        except (ValueError, AttributeError):
            return False

    @property
    def isCancelled(self) -> bool:
        try:
            status = EventStatus(self._event.strStatus)
            return status == EventStatus.CNL
        except (ValueError, AttributeError):
            return False

    @property
    def notStarted(self) -> bool:
        res = self._event.startTime > datetime.now(tz=timezone.utc)
        return res

    @property
    def hasEnded(self) -> bool:
        if self.notStarted:
            return False

        status = self._event.strStatus
        try:
            _status = EventStatus(status)
            if _status in (EventStatus.FT, EventStatus.AET, EventStatus.PPD):
                return True
            return _status == EventStatus.HT or re.match(r"^\d+", status) is not None
        except ValueError:
            return False

    def updates_(self, updated: Optional[ResponseGame]):
        if not updated:
            return None
        details = ParserDetails(None, response=updated)
        events = details.events_pixel
        return events

    def sendUpdate_(self, data, sc: SubscritionClient):
        payload = []
        if isinstance(data, list):
            payload = [d.to_dict() for d in data]
        elif hasattr(data, "to_dict"):
            payload = data.to_dict()
        logging.debug(payload)
        try:
            assert sc.group_id
            resp = post(
                f"{sc.client_id}", headers=OTP(sc.group_id).headers, json=payload
            )
            return resp.status_code
        except ConnectionError:
            logging.error(f"Cannot send update to f{sc.client_id}")
            pass

    @property
    def progressUpdate_(self):
        try:
            details = ParserDetails.get(str(self._event.details))
            assert details.game_time
            assert details.home
            assert details.away
            assert details.event_id
            return [
                DetailsEventPixel(
                    time=details.game_time,
                    action="Progress",
                    is_old_event=False,
                    score=details.score,
                    event_name=f"{details.home.name}/{details.away.name}",
                    event_id=details.event_id,
                    order=sys.maxsize,
                    status=details.game_status,
                )
            ]
        except AssertionError as e:
            logging.exception(e)

from botyo.api.footy.item.lineups import Lineups
from botyo.api.logo.team import TeamLogoPixel
from botyo.threesixfive.exception import GameNotFound
from botyo.threesixfive.item.league import LeagueImage
from .components import ScoreFormat, ScoreRow
from .livescore_details import ParserDetails
from botyo.server.output import TextOutput
from botyo.server.scheduler import Scheduler
from apscheduler.schedulers.base import JobLookupError, Job
from botyo.server.socket.connection import Connection, UnknownClientException
from botyo.server.models import RenderResult, Attachment, ZSONResponse
from botyo.threesixfive.item.models import (
    CancelJobEvent,
    DetailsEventPixel,
    Event,
    GameDetails,
    EventStatus,
    ShortGameStatus,
    ResponseGame,
    SubscriptionEvent,
    GoalEvent,
)
from botyo.server.models import ZMethod
from .player import Player
from cachable.request import Request
from enum import Enum
from hashlib import blake2b
from emoji import emojize
from datetime import datetime, timezone
import re
from requests import post
from botyo.core.otp import OTP
import sys
from pixelme import Pixelate
import time
import logging
from typing import Optional
from .goals import Goals
from botyo.goals import Query as GoalQuery
from pathlib import Path
from botyo.core.store import QueueDict, QueueList
from dataclasses import dataclass
from botyo.core.store import RedisCachable


class Headers(Enum):
    LINEUP_ANNOUNCED = "Lineup Announced"


class JobPrefix(Enum):
    INPROGRESS = "INP"
    SCHEDULED = "SCH"
    BEFOREGAME = "BFG"


class Cache(RedisCachable):

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
                assert self._struct
                self._struct.game.events = (content).events[
                    len(cached.events) :
                ]  # type: ignore
                return self._struct
            return None
        except GameNotFound:
            return None


@dataclass
class SubscriptionClient:
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
        prefix = ":".join([client, group])
        h = blake2b(digest_size=20)
        h.update(prefix.encode())
        return h.hexdigest()

    @property
    def connection(self) -> Connection:
        return Connection.client(self.client_id)

    def sendUpdate(self, data, msgId: Optional[str] = None):
        if self.is_rest:
            return self.updateREST(data)
        return self.updateBotyo(data, msgId)

    def updateBotyo(self, message, msgId: Optional[str] = None):
        result = RenderResult(
            method=ZMethod.FOOTY_SUBSCRIPTION_UPDATE, message=message, group=self.group_id
        )
        try:
            self.connection.send(
                ZSONResponse(
                    message=result.message,
                    attachment=result.attachment,
                    client=self.client_id,
                    group=result.group,
                    method=result.method,
                    plain=result.plain,
                    id=msgId,
                )
            )
        except UnknownClientException:
            pass

    def updateREST(self, data):
        payload = []
        if isinstance(data, list):
            payload = [d.to_dict() for d in data]
        elif hasattr(data, "to_dict"):
            payload = data.to_dict()
        logging.debug(payload)
        try:
            assert self.group_id
            resp = post(
                f"{self.client_id}", headers=OTP(self.group_id).headers, json=payload
            )
            return resp.status_code
        except ConnectionError:
            logging.error(f"Cannot send update to f{self.client_id}")
            pass


class SubscriptionMeta(type):

    __subs: dict[str, "Subscription"] = {}

    def __call__(cls, event: Event):
        k = event.event_hash
        if k not in cls.__subs:
            cls.__subs[k] = type.__call__(cls, event)
        return cls.__subs[k]

    def get(cls, event: Event, sc: SubscriptionClient) -> "Subscription":
        obj = cls(event)
        subs = cls.clients(event.id)
        if sc.id not in [x.id for x in subs]:
            subs.append(sc)
        return obj

    def forGroup(cls, sc: SubscriptionClient) -> list[Job]:
        res = []
        for job in Scheduler.get_jobs():
            event_id = job.id.split(":")[0]
            clients = cls.clients(event_id)
            if sc.id in [x.id for x in clients]:
                res.append(job)
        return res

    def clients(cls, event_id: str) -> QueueList:
        return QueueList(f"subscription.{event_id}.clients")


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
        return ":".join([self._event.id, prefix.value])

    @property
    def beforeGameId(self):
        prefix = JobPrefix.BEFOREGAME
        return ":".join([self._event.id, prefix.value])

    @property
    def event_name(self):
        return " vs ".join(
            [self._event.strHomeTeam.upper(), self._event.strAwayTeam.upper()]
        )

    @property
    def goals_queue(self) -> QueueDict:
        return QueueDict(f"subscription.{self._event.id}.goals.queue")

    @property
    def subscriptions(self) -> list[SubscriptionClient]:
        return __class__.clients(self._event.id)

    def cancel(self, sc: SubscriptionClient):
        try:
            if sc.is_rest:
                sc.sendUpdate(CancelJobEvent(job_id=self.id), self.id)
            self.subscriptions.remove(sc)
            if not len(self.subscriptions):
                Scheduler.cancel_jobs(self.id)
        except JobLookupError:
            pass

    def cancel_all(self):
        for sc in self.subscriptions:
            self.cancel(sc)
        for gid in list(self.goals_queue.keys()):
            gq = self.goals_queue[gid]
            if gq.event_id == self._event.idEvent:
                del self.goals_queue[gid]

    def sendGoal(self, message: str, attachment: Path):
        for sc in self.subscriptions:
            if sc.is_rest:
                continue
            result = RenderResult(
                method=ZMethod.FOOTY_SUBSCRIPTION_UPDATE,
                message=message,
                attachment=Attachment(
                    path=attachment.as_posix(),
                    contentType="video/mp4",
                ),
                group=sc.group_id,
            )
            try:
                sc.connection.send(
                    ZSONResponse(
                        message=result.message,
                        attachment=result.attachment,
                        client=sc.client_id,
                        group=result.group,
                        method=result.method,
                        plain=result.plain,
                        id=self.id
                    )
                )
            except UnknownClientException:
                pass

    def processGoals(self, game: GameDetails):
        try:
            events = game.events
            assert isinstance(events, list)
            for x in events:
                if x.is_goal:
                    logging.debug(f"GOAL event at {self.event_name}")
                    goal_query = GoalQuery(
                        event_name=self.event_name,
                        event_id=int(self._event.idEvent),
                        game_event_id=x.order_id,
                        score=game.score,
                        home=self._event.strHomeTeam.lower(),
                        away=self._event.strAwayTeam.lower(),
                        timestamp=int(time.time()),
                        player=x.playerName,
                    )
                    goal_event = GoalEvent(
                        event_id=int(self._event.idEvent),
                        event_name=self.event_name,
                        game_event_id=x.order_id,
                        player=x.playerName,
                        score=game.score,
                        time=x.displayTime,
                    )
                    Goals.save_metadata(goal_event)
                    Goals.monitor(goal_query)
                    self.goals_queue[goal_query.id] = goal_query
        except AssertionError as e:
            logging.exception(e)
            pass

    def checkGoals(self, updated: Optional[ResponseGame] = None):
        try:
            assert updated
            assert updated.game
            if updated.game.events:
                self.processGoals(updated.game)
        except AssertionError:
            pass
        Goals.poll()
        for qid in list(self.goals_queue.keys()):
            gq = self.goals_queue[qid]
            if goal_video := Goals.video(gq):
                self.sendGoal(gq.title, goal_video)
                del self.goals_queue[qid]

    def trigger(self):
        try:
            assert self._event.details
            cache = Cache(url=self._event.details, jobId=self.id)
            updated = cache.update
            chatUpdate = self.updates(updated)
            for sc in self.subscriptions:
                if sc.is_rest:
                    try:
                        details = ParserDetails(None, response=updated)
                        events = details.events_pixel
                        sc.sendUpdate(events, self.id)
                    except Exception:
                        pass
                    if cache.halftime:
                        cache.halftime = False
                        sc.sendUpdate(self.halftimeAnnoucementPixel, self.id)
                    else:
                        sc.sendUpdate(self.progressUpdatePixel, self.id)
                elif chatUpdate:
                    TextOutput.clean()
                    TextOutput.addRows(chatUpdate)
                    try:
                        sc.sendUpdate(TextOutput.render(), self.id)
                    except UnknownClientException:
                        pass
            self.checkGoals(updated)
            content = cache.content
            assert content
            # if not content:
            #     raise ValueError
            #     # return self.cancel_all()
            Player.store(content.game)
            if any(
                [
                    ShortGameStatus(content.game.shortStatusText)
                    in [ShortGameStatus.FINAL, ShortGameStatus.AFTER_PENALTIES],
                ]
            ):
                for sc in self.subscriptions:
                    try:
                        if sc.is_rest:
                            sc.sendUpdate(self.fulltimeAnnoucementPixel, self.id)
                        else:
                            sc.sendUpdate(self.fulltimeAnnoucement, self.id)
                    except UnknownClientException:
                        pass
                    if content.game.justEnded:
                        self.cancel(sc)
                        logging.debug(f"subscription {self.event_name} in done")
        except AssertionError:
            pass
        except ValueError as e:
            logging.exception(e)
        except Exception as e:
            logging.exception(e)
            # return self.cancel_all()

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
            assert details.
            res = ScoreRow(
                status=f'{details.game_time:.0f}"',
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
        logging.debug(f"FOOT SUB: Full Time {self.event_name}")
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
            return DetailsEventPixel.fullTimeEvent(
                details=details, league_id=self._event.idLeague
            )
        except AssertionError as e:
            logging.exception(e)

    @property
    def halftimeAnnoucementPixel(self):
        try:
            details = ParserDetails.get(str(self._event.details))
            return DetailsEventPixel.halfTimeEvent(details, self._event.idLeague)
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
        return [
            DetailsEventPixel.startTimeEvent(
                event_name=self.event_name,
                event_id=self._event.idEvent,
                league_id=self._event.idLeague,
                home_id=self._event.idHomeTeam,
                away_id=self._event.idAwayTeam,
            )
        ]

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
                        sc.sendUpdate(self.startAnnouncementPixel, self.id)
                    else:
                        sc.sendUpdate(self.startAnnouncement, self.id)
                except UnknownClientException:
                    pass

    def schedule(self, sc: SubscriptionClient):
        if sc.is_rest:
            logo = LeagueImage(self._event.idLeague)
            logo_path = logo.path
            pix = Pixelate(input=logo_path, padding=200, grid_lines=True, block_size=25)
            pix.resize((8, 8))
            sc.sendUpdate(
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
                self.id,
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
                    sc.sendUpdate(text, self.id)
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
            return any(
                [_status == EventStatus.HT, re.match(r"^\d+", status) is not None]
            )
        except ValueError:
            return False

    def updates_(self, updated: Optional[ResponseGame]):
        if not updated:
            return None
        details = ParserDetails(None, response=updated)
        events = details.events_pixel
        return events

    @property
    def progressUpdatePixel(self):
        try:
            details = ParserDetails.get(str(self._event.details))
            assert details.game_time
            assert details.home
            assert details.away
            assert details.event_id
            return [
                DetailsEventPixel(
                    id=self._event.id,
                    time=details.game_time,
                    action="Progress",
                    is_old_event=False,
                    score=details.score,
                    event_name=f"{details.home.name}/{details.away.name}",
                    event_id=self._event.idEvent,
                    order=sys.maxsize,
                    status=details.game_status,
                    league_id=self._event.idLeague,
                    home_team_id=details.home.id,
                    away_team_id=details.away.id,
                )
            ]
        except AssertionError:
            pass

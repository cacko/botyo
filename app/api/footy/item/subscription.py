
from app.api.footy.item.lineups import Lineups
from app.api.logo.team import TeamLogoPixel
from app.threesixfive.exception import GameNotFound
from app.threesixfive.item.league import LeagueImage
from .components import ScoreFormat, ScoreRow
from .livescore_details import ParserDetails
from botyo_server.output import TextOutput
from botyo_server.scheduler import Scheduler
from botyo_server.socket.connection import Connection, UnknownClientException
from botyo_server.models import RenderResult
from app.threesixfive.item.models import (
    CancelJobEvent,
    DetailsEventPixel,
    Event,
    EventStatus,
    GameStatus,
    ResponseGame,
    SubscriptionEvent
)
from app.api import ZMethod
from .player import Player
from cachable.request import Request
from cachable.cacheable import Cachable
from enum import Enum
from hashlib import blake2b
from apscheduler.job import Job
from emoji import emojize
from datetime import datetime, timezone
import re
from requests import post
from app.core.otp import OTP
import sys
from pixelme import Pixelate
import time
import logging


class Headers(Enum):
    LINEUP_ANNOUNCED = "Lineup Announced"


class JobPrefix(Enum):
    INPROGRESS = "INP"
    SCHEDULED = "SCH"
    BEFOREGAME = "BFG"


class Cache(Cachable):

    _struct: ResponseGame = None
    __url: str = None
    __jobId: str = None
    __id: str = None
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

    def fetch(self) -> ResponseGame:
        url = f"{self.__url}&{time.time()}"
        req = Request(url)
        try:
            json =  req.json
            response: ResponseGame = ResponseGame.from_dict(json)
            return response
        except Exception as e:
            print(e)
            return None

    @property
    def content(self) -> ResponseGame:
        isLoaded =  self.load()
        if not isLoaded:
            fetch =  self.fetch()
            self._struct = self.tocache(fetch)
        return self._struct

    @property
    def fresh(self) -> ResponseGame:
        fresh =  self.fetch()
        self._struct = self.tocache(fresh)
        if not self._struct:
            raise GameNotFound
        return self._struct


    @property
    def update(self) -> ResponseGame:
        try:
            cached =  self.fromcache()
            if not cached:
                return  self.fresh
            fresh =  self.fresh
            if cached.status != fresh.status and fresh.status == 'HT':
                self.halftime = True
            if len(cached.events) < len(fresh.events):
                content =  self.content
                self._struct.game.events = (content).events[
                    len(cached.events):
                ]
                return self._struct
            return None
        except GameNotFound:
            return None


class SubscriptionMeta(type):

    def __call__(cls, event: Event, client: str, group, *args, **kwds):
        return type.__call__(cls, event, client, group, *args, **kwds)

    def forGroup(cls, client: str, group) -> list[Job]:
        prefix = cls.jobPrefix(client, group)
        return list(
            filter(
                lambda g: g.id.startswith(prefix),
                Scheduler.get_jobs()
            )
        )

    def jobPrefix(cls, client: str, group) -> str:
        prefix = ":".join([
            cls.__module__,
            client,
            group
        ])
        h = blake2b(digest_size=20)
        h.update(prefix.encode())
        return h.hexdigest()


class Subscription(metaclass=SubscriptionMeta):

    _event: Event = None
    _groupId = None
    _clientId: str = None
    _announceLineups = False

    def __init__(self, event: Event, client: str, group) -> None:
        self._clientId = client
        self._event = event
        self._groupId = group

    @property
    def id(self):
        prefix = JobPrefix.INPROGRESS
        if not self.inProgress:
            prefix = JobPrefix.SCHEDULED
        jobPrefix = __class__.jobPrefix(self._clientId, self._groupId)
        return ":".join([
            jobPrefix,
            self._event.id,
            prefix.value
        ])

    @property
    def beforeGameId(self):
        prefix = JobPrefix.BEFOREGAME
        jobPrefix = __class__.jobPrefix(self._clientId, self._groupId)
        return ":".join([
            jobPrefix,
            self._event.id,
            prefix.value
        ])

    @property
    def event_name(self):
        return " vs ".join([
            self._event.strHomeTeam.upper(),
            self._event.strAwayTeam.upper()
        ])

    def cancel(self, notify=False):
        Scheduler.cancel_jobs(self.id)
        if notify and self._clientId.startswith("http"):
             self.sendUpdate_(CancelJobEvent(job_id=self.id))

    def sendUpdate(self, message):
        if self._clientId.startswith("http"):
            return  self.sendUpdate_(message)
        if not self.client:
            return
        connection = self.client
        if not self.client:
            raise UnknownClientException
        connection.respond(
            RenderResult(
                method=ZMethod.FOOTY_SUBSCRIBE,
                message=message,
                group=self._groupId
            )
        )

    def trigger(self):
        if self._clientId.startswith("http"):
            return  self.trigger_()
        if not self.client:
            logging.debug(
                f">> skip schedule {self._clientId}")
            return
        cache = Cache(
            url=self._event.details,
            jobId=self.id
        )
        updated =  cache.update
        if update := self.updates(updated):
            TextOutput.addRows(update)
            try:
                 self.sendUpdate(TextOutput.render())
            except UnknownClientException:
                pass
        try:
            content =  cache.content
            if not content:
                return  self.cancel(True)
            Player.store(content.game)
            logging.debug(content.game.shortStatusText)
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
                try:
                     self.sendUpdate( self.fulltimeAnnoucement)
                except UnknownClientException:
                    pass
                self.cancel()
                logging.debug(f"subscription {self.event_name} in done")
        except ValueError:
            pass
        except Exception as e:
            logging.exception(e)
            return  self.cancel(True)

    def updates(self, updated: ResponseGame) -> list[str]:
        if self._clientId.startswith("http"):
            return self.updates_(updated)
        if not updated:
            return None
        details = ParserDetails(None, response=updated)

        rows = details.rendered
        if not rows:
            return None
        res = ScoreRow(
            status=f"{details.game_time:.0f}",
            home=details.home.name,
            away=details.away.name,
            score=details.score,
            format=ScoreFormat.STANDALONE,
            league=self._event.strLeague
        )
        return [*rows, res]

    @property
    def client(self) -> Connection:
        try:
            return Connection.client(self._clientId)
        except UnknownClientException:
            return None

    @property
    def fulltimeAnnoucement(self) -> str:
        self.cancel()
        logging.debug(f"subscription {self.event_name} in done")
        if self._clientId.startswith("http"):
            return  self.fulltimeAnnoucement_
        details =  ParserDetails.get(self._event.details)
        icon = emojize(':chequered_flag:')
        TextOutput.addRows([
            " ".join([
                icon,
                "FULLTIME: ",
                self.event_name,
                details.score
            ])
        ])

        return TextOutput.render()

    @property
    def startAnnouncement(self) -> str:
        if self._clientId.startswith("http"):
            return self.startAnnouncement_
        TextOutput.addRows([
            " ".join([
                emojize(':goal_net:'),
                f"GAME STARTING: {self.event_name}"
            ])
        ])
        return TextOutput.render()

    @property
    def startAnnouncement_(self) -> str:
        return [DetailsEventPixel(
            time=0,
            action='Game Start',
            order=0,
            is_old_event=False,
            event_name=self.event_name,
            event_id=self._event.id
        )]

    def start(self, announceStart=False):
        logging.debug(f"subscriion in live mode {self.event_name}")
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.trigger,
            trigger="interval",
            seconds=60,
            replace_existing=True,
            misfire_grace_time=60
        )
        if announceStart:
            try:
                self.sendUpdate(self.startAnnouncement)
            except UnknownClientException:
                pass

    def schedule(self):
        if self._clientId.startswith("http"):
            logo = LeagueImage(self._event.idLeague)
            logo_path =  logo.path
            pix = Pixelate(
                input=logo_path,
                padding=200,
                grid_lines=True,
                block_size=25
            )
            pix.resize((8, 8))
            self.sendUpdate_(SubscriptionEvent(
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
                status=self._event.displayStatus
            ))
        if self.inProgress:
            return  self.start()
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.start,
            trigger="date",
            replace_existing=True,
            run_date=self._event.startTime,
            kwargs={"announceStart": True},
            misfire_grace_time=180
        )

    def beforeGameTrigger(self):
        if not self.client:
            logging.debug(
                f">> skip schedule {self._clientId}")
            return
        try:
            logging.debug(f"{self.event_name} check for lineups")
            lineups = Lineups(self._event)
            message =  lineups.message
            if not message:
                logging.debug(f"{self.event_name} not lineups yet")
                return
            logging.debug(f"{self.event_name} lineups available")
            TextOutput.addRows([
                f"{Headers.LINEUP_ANNOUNCED.value: ^ 42}\n".upper(),
                message
            ])
            text = TextOutput.render()
            try:
                self.sendUpdate(text)
            except UnknownClientException:
                pass
            Scheduler.cancel_jobs(self.beforeGameId)
            logging.debug(f"subscription before game {self.event_name} in done")
        except ValueError:
            pass
        except Exception as e:
            logging.exception(e)

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
            return _status == EventStatus.HT or re.match(r"^\d+", status)
        except ValueError:
            return False

    def updates_(self, updated: ResponseGame) -> list[str]:
        if not updated:
            return None
        details = ParserDetails(None, response=updated)
        events = details.events_pixel
        return events

    def sendUpdate_(self, data):
        payload = []
        if isinstance(data, list):
            payload = [d.to_dict() for d in data]
        elif hasattr(data, 'to_dict'):
            payload = data.to_dict()
        logging.debug(payload)
        try:
            resp = post(
                f"{self._clientId}",
                headers=OTP(self._groupId).headers,
                json=payload
            )
            return resp.status_code
        except ConnectionError:
            logging.error(f"Cannot send update to f{self._clientId}")
            pass

    @property
    def fulltimeAnnoucement_(self) -> str:
        details = ParserDetails.get(self._event.details)
        return [DetailsEventPixel(
            time=details.game_time,
            action='Full Time',
            is_old_event=False,
            score=details.score,
            event_name=f"{details.home.name}/{details.away.name}",
            event_id=details.event_id,
            order=sys.maxsize
        )]

    @property
    def halftimeAnnoucement_(self) -> str:
        details = ParserDetails.get(self._event.details)
        return [DetailsEventPixel(
            time=details.game_time,
            action='Half Time',
            is_old_event=False,
            score=details.score,
            event_name=f"{details.home.name}/{details.away.name}",
            event_id=details.event_id,
            order=sys.maxsize
        )]

    @property
    def progressUpdate_(self) -> str:
        details = ParserDetails.get(self._event.details)
        return [DetailsEventPixel(
            time=details.game_time,
            action='Progress',
            is_old_event=False,
            score=details.score,
            event_name=f"{details.home.name}/{details.away.name}",
            event_id=details.event_id,
            order=sys.maxsize
        )]

    def trigger_(self):
        cache = Cache(
            url=self._event.details,
            jobId=self.id
        )
        updated =  cache.update
        if update := self.updates_(updated):
            try:
                self.sendUpdate_(update)
            except UnknownClientException as e:
                print(e)
        
        if cache.halftime:
            cache.halftime = False
            self.sendUpdate( self.halftimeAnnoucement_)
        else:
            self.sendUpdate( self.progressUpdate_)
        try:
            content =  cache.content
            if not content:
                return  self.cancel(True)
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
                try:
                    self.sendUpdate( self.fulltimeAnnoucement)
                except UnknownClientException as e:
                    logging.error(e)
                    pass
        except ValueError:
            pass
        except Exception as e:
            logging.exception(e)
            return self.cancel(True)

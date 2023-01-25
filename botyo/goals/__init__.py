from you_get.extractors.twitter import twitter_download
from botyo.core.config import Config as app_config
from typing import Optional, Any, Generator
from .twitter import Twitter
from pathlib import Path
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from fuzzelinho import MatchMethod, Match
import logging
import re
from botyo.threesixfive.item.models import GoalEvent
from datetime import datetime, timedelta
from botyo.core.store import QueueDict

GOAL_MATCH = re.compile(r"^([\w ]+)\[?(\d+)]?\s-\s\[?(\d+)]?\s*([^\r\n ]+)", re.IGNORECASE)
VIDEO_MATCH = re.compile(r"^video-(\d+)-(\d+)\.mp4")
GOAL_CHECK_EXPIRATION = timedelta(minutes=15)

# (base) muzak at /store/cache/znayko/goals ❯ ffprobe -v error -show_entries stream=width,height -of default=noprint_wrappers=1 GoalsZack\ \[1597676886527995904\].mp4
# width=1280
# height=720


class TeamsMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO
    exact_fields = ["score"]


@dataclass_json
@dataclass
class TeamsNeedle:
    home: str
    away: str
    score: str


@dataclass_json
@dataclass
class GoalNeedle:
    home: int
    away: int


@dataclass_json
@dataclass
class TwitterNeedle:
    needle: TeamsNeedle
    goals: GoalNeedle
    id: str
    text: str
    url: str


@dataclass
class DownloadItem:
    text: str
    url: str
    id: str
    path: Path
    event_id: int
    game_event_id: int

    @property
    def filename(self) -> str:
        return __class__.get_filename(self.event_id, self.game_event_id)

    def rename(self, storage_dir: Path) -> "DownloadItem":
        dp = storage_dir / self.filename
        if not dp.exists():
            dp = self.path.rename(dp)
            logging.debug(f"GOALS rename {self.path} to {dp}")
        return __class__(
            text=self.text,
            url=self.url,
            id=self.id,
            path=dp,
            event_id=self.event_id,
            game_event_id=self.game_event_id,
        )

    @classmethod
    def get_filename(cls, event_id: int, game_event_id: int) -> str:
        return f"video-{event_id}-{game_event_id}.mp4"

    @classmethod
    def get_metafile(cls, event_id: int, game_event_id: int) -> str:
        return f"video-{event_id}-{game_event_id}.json"

    @classmethod
    def from_path(cls, video_path: Path) -> Optional["DownloadItem"]:
        match = VIDEO_MATCH.match(video_path.name)
        if not match:
            return None
        event_id, game_event_id = map(int, match.groups())


@dataclass_json
@dataclass
class Query:
    event_name: str
    event_id: int
    game_event_id: int
    home: str
    away: str
    score: str
    timestamp: int
    player: Optional[str] = None

    @property
    def title(self) -> str:
        res = f"{self.home} - {self.away} {self.score}"
        if self.player:
            res += f" [{self.player}]"
        return res

    @property
    def goals(self) -> list[int]:
        return [int(x) for x in self.score.split(":")]

    @property
    def id(self) -> str:
        return f"{self.event_id}-{self.game_event_id}"

    @property
    def goal_video(self) -> str:
        return DownloadItem.get_filename(self.event_id, self.game_event_id)

    @property
    def is_expired(self) -> bool:
        try:
            return (
                datetime.now() - datetime.fromtimestamp(self.timestamp)
                > GOAL_CHECK_EXPIRATION
            )
        except AssertionError:
            return False


class Goal:
    def __init__(self) -> None:
        pass


class GoalsMeta(type):

    __instance: Optional["Goals"] = None

    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    def goals(cls, query: list[Query]) -> Generator[DownloadItem, None, None]:
        yield from cls().do_search(query)

    def videos(cls) -> list[DownloadItem]:
        return cls().get_downloads()

    @property
    def output_dir(cls) -> Path:
        root = Path(app_config.cachable.path) / "goals"
        if not root.exists():
            root.mkdir(parents=True)
        return root

    def goal_video(cls, q: Query) -> Optional[Path]:
        fp = cls.output_dir / \
            DownloadItem.get_filename(q.event_id, q.game_event_id)
        if fp.exists():
            logging.debug(f"GOAL found at {fp}")
            return fp
        return None

    def save_data(cls, data: GoalEvent) -> bool:
        fp = cls.output_dir / DownloadItem.get_metafile(
            data.event_id, data.game_event_id
        )
        if fp.exists():
            return True
        return fp.write_text(data.to_json()) > 0  # type: ignore


class Goals(object, metaclass=GoalsMeta):

    __videoData: Optional[QueueDict] = None

    @property
    def video_data(self) -> QueueDict:
        if not self.__videoData:
            self.__videoData = QueueDict("video.data")
        return self.__videoData

    def __fetch(self, **kwds):
        tweets = Twitter.media(**kwds)
        for t in tweets:
            t_id, t_text = (
                t.tweet.id if t.tweet.id else "",
                t.tweet.text if t.tweet.text else "",
            )
            logging.debug(f"TWEET -> {t_text}")
            if matched_teams := GOAL_MATCH.search(t_text):
                team1, score1, score2, team2 = map(
                    str.strip, matched_teams.groups())
                try:
                    twitter_download(
                        url=t.url, output_dir=__class__.output_dir.as_posix(), merge=True
                    )
                except Exception as e:
                    logging.error(f"TWITTER DOWNLOAD: {e}")
                self.video_data[t_id] = TwitterNeedle(
                    needle=TeamsNeedle(
                        home=team1.lower(), away=team2.lower(), score=f"{score1}:{score2}"),
                    goals=GoalNeedle(home=int(score1), away=int(score2)),
                    id=t_id,
                    text=t_text,
                    url=t.url,
                )

    def do_search(
        self, query: list[Query], **kwds
    ) -> Generator[DownloadItem, None, None]:
        matcher = TeamsMatch(haystack=query)
        try:
            self.__fetch(**kwds)
        except Exception as e:
            logging.error(f"FETCH ERROR {e}")
        for needle in list(self.video_data.values()):
            for dp in __class__.output_dir.glob(f"*[[]{needle.id}[]].mp4"):
                matched: list[Query] = matcher.fuzzy(needle.needle)
                for q in matched:
                    yield DownloadItem(
                        text=needle.text,
                        url=needle.url,
                        id=q.id,
                        path=dp.absolute(),
                        game_event_id=q.game_event_id,
                        event_id=q.event_id,
                    )
                    try:
                        del self.video_data[needle.id]
                    except KeyError:
                        pass

    def get_downloads(self) -> list[DownloadItem]:
        return []
        # for dp in __class__.output_dir.glob(f"*.mp4"):
        #     return []

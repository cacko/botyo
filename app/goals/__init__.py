from you_get.extractors.twitter import twitter_download
from app.core.config import Config as app_config
from typing import Optional, Any, Generator
from .twitter import Twitter
from pathlib import Path
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from fuzzelinho import MatchMethod, Match
import logging
import re
from app.threesixfive.item.models import GoalEvent
import json
from requests.exceptions import HTTPError

GOAL_MATCH = re.compile(r"([\w ]+)\s\d+\s-\s\d+\s([\w ]+)", re.MULTILINE)
VIDEO_MATCH = re.compile(r"^video-(\d+)-(\d+)\.mp4")


class TeamsMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class TeamsNeedle:
    home: str
    away: str


@dataclass_json
@dataclass
class TwitterNeedle:
    needle: TeamsNeedle
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
        return self.__class__.get_filename(self.event_id, self.game_event_id)

    def rename(self, storege_dir: Path):
        dp = storege_dir / self.filename
        if not dp.exists():
            self.path = self.path.rename(dp)
        else:
            self.path = dp

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
    title: str

    @property
    def needles(self) -> list[str]:
        if " vs " in self.event_name:
            return [*map(str.strip, self.event_name.split(" vs "))]
        return [*map(str.strip, self.event_name.split("/"))]

    @property
    def id(self) -> str:
        return f"{self.event_id}-{self.game_event_id}"

    @property
    def home(self) -> str:
        return self.needles[0]

    @property
    def away(self) -> str:
        return self.needles[1]

    @property
    def goal_video(self) -> str:
        return DownloadItem.get_filename(self.event_id, self.game_event_id)


class Goal:
    def __init__(self) -> None:
        pass


class GoalsMeta(type):

    __instance: Optional["Goals"] = None

    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    def goals(cls, query: list[Query]) -> list[DownloadItem]:
        return list(cls().do_search(query))

    def videos(cls) -> list[DownloadItem]:
        return cls().get_downloads()

    @property
    def output_dir(cls) -> Path:
        root = Path(app_config.cachable.path) / "goals"
        if not root.exists():
            root.mkdir(parents=True)
        return root

    def goal_video(cls, q: Query) -> Optional[Path]:
        fp = cls.output_dir / DownloadItem.get_filename(q.event_id, q.game_event_id)
        if fp.exists():
            logging.info(f"GOAL found at {fp}")
            return fp
        logging.error(f"GOAL NOT found at {fp}")
        return None

    def save_data(cls, data: GoalEvent) -> bool:
        fp = cls.output_dir / DownloadItem.get_metafile(
            data.event_id, data.game_event_id
        )
        if fp.exists():
            return True
        return fp.write_text(data.to_json()) > 0  # type: ignore


class Goals(object, metaclass=GoalsMeta):
    def __needles(self, **kwds) -> Generator[TwitterNeedle, None, None]:
        for t in Twitter.media(**kwds):
            t_id, t_text = (
                t.tweet.id if t.tweet.id else "",
                t.tweet.text if t.tweet.text else "",
            )
            matched_teams = GOAL_MATCH.search(t_text.replace("[", "").replace("]", ""))
            if not matched_teams:
                continue
            teams = [*map(lambda x: x.strip().lower(), matched_teams.groups())]
            logging.debug(f"GOALS: matched teams {teams}")
            yield TwitterNeedle(
                needle=TeamsNeedle(home=teams[0], away=teams[1]),
                id=t_id,
                text=t_text,
                url=t.url,
            )

    def do_search(
        self, query: list[Query], **kwds
    ) -> Generator[DownloadItem, None, None]:
        for needle in self.__needles(**kwds):
            try:
                twitter_download(url=needle.url, output_dir=__class__.output_dir.as_posix())
            except HTTPError as e:
                logging.error(e)
            except Exception as e:
                logging.exception(e)
            for dp in __class__.output_dir.glob(f"*{needle.id}*"):
                if dp.suffix.lower() != ".mp4":
                    dp.unlink(missing_ok=True)
                    continue
                matcher = TeamsMatch(query)
                matched: list[Query] = matcher.fuzzy(needle.needle)
                if not len(matched):
                    dp.unlink(missing_ok=True)
                    continue
                for q in matched:
                    di = DownloadItem(
                        text=needle.text,
                        url=needle.url,
                        id=needle.id,
                        path=dp,
                        game_event_id=q.game_event_id,
                        event_id=q.event_id,
                    )

                    di.rename(__class__.output_dir)
                    yield di

    def get_downloads(self) -> list[DownloadItem]:
        return []
        # for dp in __class__.output_dir.glob(f"*.mp4"):
        #     return []

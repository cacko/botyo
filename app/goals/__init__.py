from you_get.extractors.twitter import twitter_download
from app.core.config import Config as app_config
from typing import Optional, Any, Generator
from .twitter import Twitter
from pathlib import Path
from dataclasses import dataclass

import re

GOAL_MATCH = re.compile(r"([\w ]+)\s\d+\s-\s\d+\s([\w ]+)", re.MULTILINE)



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
        self.path = self.path.rename(dp)
        
    @classmethod
    def get_filename(cls, event_id:int, game_event_id: int) -> str:
        return f"video-{event_id}-{game_event_id}.mp4"


@dataclass
class Query:
    event_name: str
    event_id: int
    game_event_id: int

    @property
    def needles(self) -> list[str]:
        if " vs " in self.event_name:
            return [*map(str.strip, self.event_name.split(" vs "))]
        return [*map(str.strip, self.event_name.split("/"))]
    
    @property
    def id(self) -> str:
        return f"{self.event_id}-{self.game_event_id}"


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

    @property
    def output_dir(cls) -> Path:
        return Path(app_config.cachable.path)
    
    def goal_video(cls, q: Query) -> Optional[Path]:
        fp = cls.output_dir / DownloadItem.get_filename(q.event_id, q.game_event_id)
        if fp.exists():
            return fp
        return None


class Goals(object, metaclass=GoalsMeta):
    def do_search(
        self, query: list[Query], **kwds
    ) -> Generator[DownloadItem, None, None]:

        for t in Twitter.media(**kwds):
            try:
                twitter_download(url=t.url, output_dir=__class__.output_dir.as_posix())
                t_id, t_text = (
                    t.tweet.id if t.tweet.id else "",
                    t.tweet.text if t.tweet.text else "",
                )
                for dp in __class__.output_dir.glob(f"*{t_id}*"):
                    if dp.suffix.lower() != ".mp4":
                        dp.unlink(missing_ok=True)
                        continue
                    for q in query:
                        if m := GOAL_MATCH.search(t_text.replace("[", "").replace("]", "")):
                            teams = m.groups()
                            if any([qi in teams for qi in query]):
                                di = DownloadItem(
                                    text=t_text,
                                    url=t.url,
                                    id=t_id,
                                    path=dp,
                                    game_event_id=q.game_event_id,
                                    event_id=q.event_id,
                                )
                                di.rename(__class__.output_dir)
                                yield di
            except Exception:
                pass

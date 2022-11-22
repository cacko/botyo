from you_get.extractors.twitter import twitter_download
from app.core.config import Config as app_config
from typing import Optional, Any, Generator
from .twitter import Twitter
from pathlib import Path
from dataclasses import dataclass
from functools import reduce

# text=USA 1 - [1] Wales - Gareth Bale penalty 82'


@dataclass
class DownloadItem:
    text: str
    url: str
    id: str
    path: Path
    matches: list[str]


class Goal:
    def __init__(self) -> None:
        pass


class GoalsMeta(type):

    __instance: Optional["Goals"] = None

    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    def goals(cls, query: list[str]) -> list[DownloadItem]:
        return list(cls().do_search(query))

    @property
    def output_dir(cls) -> Path:
        return Path(app_config.cachable.path)


class Goals(object, metaclass=GoalsMeta):
    def do_search(
        self, query: list[str], **kwds
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
                    matches = reduce(
                        lambda r, w: [*r, *([w] if w in t_text.lower() else [])],
                        map(str.lower, query),
                        [],
                    )
                    if len(matches):
                        yield (
                            DownloadItem(
                                text=t_text,
                                url=t.url,
                                id=t_id,
                                path=dp,
                                matches=matches,
                            )
                        )
            except Exception:
                pass

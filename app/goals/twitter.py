from typing import Any, Optional, Generator

from pytwitter import Api
from pytwitter.models import User, Tweet, Response

from app.core.config import Config as app_config
import logging

from dataclasses import dataclass


@dataclass
class TwitterItem:
    tweet: Tweet
    url: str


class TwitterMeta(type):
    __instance: Optional["Twitter"] = None

    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    @property
    def default_username(cls):
        return app_config.goals.twitter

    def media(cls, **kwds) -> list[TwitterItem]:
        result = []
        args = {
            "exclude": "retweets,replies",
            "media_fields": "url,height",
            "expansions": ["attachments.media_keys"],
            "tweet_fields": "attachments",
        }

        for t in cls().get_user_timeline(**{**kwds, **args}):
            logging.info(t.tweet)
            try:
                assert t.tweet.attachments
                result.append(t)
            except AssertionError:
                pass
        return result


class Twitter(object, metaclass=TwitterMeta):

    __api: Optional[Api] = None
    __users: dict[str, User] = {}
    __timeline_since_id: dict[str, str] = {}

    @property
    def api(self) -> Api:
        if not self.__api:
            self.__api = Api(
                consumer_key=app_config.goals.api_key,
                consumer_secret=app_config.goals.api_secret,
                access_token=app_config.goals.access_token,
                access_secret=app_config.goals.access_secret,
            )
        return self.__api

    def get_user(self, username: str) -> User:
        if username not in self.__users:
            res = self.api.get_user(username=username).data  # type: ignore
            assert isinstance(res, User)
            self.__users[username] = res
        return self.__users[username]

    def get_user_timeline(self, **kwds) -> Generator[TwitterItem, None, None]:
        user = self.get_user(kwds.get("username", __class__.default_username))
        assert user.id
        assert user.username
        if since_id := self.__timeline_since_id.get(user.username, ""):
            kwds["since_id"] = since_id
        res = self.api.get_timelines(user_id=user.id, **kwds)
        assert isinstance(res, Response)
        tweets = res.data
        ids = []
        assert isinstance(tweets, list)
        for t in tweets:
            try:
                assert isinstance(t, Tweet)
                assert isinstance(t.text, str)
                assert isinstance(t.id, str)
                ids.append(int(t.id))
                yield TwitterItem(
                    tweet=t,
                    url=f"https://twitter.com/{user.username}/status/{t.id}",
                )
            except AssertionError as e:
                logging.exception(e)
                pass
        self.__timeline_since_id[user.username] = max(ids)

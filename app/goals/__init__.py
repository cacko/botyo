from you_get.extractors.twitter import twitter_download
from app.core.config import Config as app_config
from typing import Optional, Any
from .twitter import Twitter
import logging

class GoalsMeta(type):
    
    __instance: Optional['Goals'] = None
    
    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance
    
    def goals(cls, query: list[str]):
        return cls().do_search(query)
    
    
class Goals(object, metaclass=GoalsMeta):
    
    def do_search(self, query: list[str], **kwds):
        res = Twitter.media(**kwds)
        for t in res:
            try:
                v = twitter_download(url=t.url)
                logging.warning(type(v))
            except Exception:
                pass
        return res
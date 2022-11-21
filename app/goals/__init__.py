import you_get
from you_get.common import any_download
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
        res = Twitter.media(query, **kwds)
        for t in res:
            try:
                v = any_download(url=t.url, output_dir="/Volumes/Devo/Code/znayko")
                logging.info(v)
            except Exception:
                pass
        return res
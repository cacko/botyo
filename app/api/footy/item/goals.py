from typing import Optional, Any
from app.goals import Goals as GoalsGenerator, Query as GoalQuery
from datetime import datetime, timedelta
import logging

class GoalsMeta(type):
    
    __instance: Optional['Goals'] = None
    
    
    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwds)
        return cls.__instance

    def monitor(cls, query: GoalQuery):
        cls().do_monitor(query)
    
    def poll(cls):
        return cls().do_updates()


class Goals(object, metaclass=GoalsMeta):
    
    __last_update: datetime = datetime.fromtimestamp(0)
    __interval: timedelta = timedelta(minutes=2)
    __query: dict[str, GoalQuery] = {}
    
    def do_monitor(self, query: GoalQuery):
        self.__query[query.id] = query
        logging.info(f"GOALS: added {'/'.join(query.needles)} to query")
        logging.info(f"GOALS: {self.__query}")
        
    def do_updates(self):
        if not len(self.__query):
            return
        if (datetime.now() - self.__last_update) < self.__interval:
            return []
        self.__last_update = datetime.now()
        for vi in GoalsGenerator.goals(list(self.__query.values())):
            try:
                del self.__query[vi.id]
            except KeyError:
                pass
            logging.info(vi)
                
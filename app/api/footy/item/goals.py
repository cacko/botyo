from typing import Optional, Any
from app.goals import Goals as GoalsGenerator, Query as GoalQuery
from datetime import datetime, timedelta
import logging
from pathlib import Path
from app.threesixfive.item.models import GoalEvent
from app.core.store import QueueDict

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
    
    def video(cls, query: GoalQuery) -> Optional[Path]:
        return GoalsGenerator.goal_video(query);
    
    def save_metadata(cls, data: GoalEvent) -> bool:
        return GoalsGenerator.save_data(data)


class Goals(object, metaclass=GoalsMeta):
    
    __last_update: datetime = datetime.fromtimestamp(0)
    __interval: timedelta = timedelta(minutes=2)
    
    @property
    def queue(self) -> QueueDict:
        return QueueDict("goals.queue")
    
    def do_monitor(self, query: GoalQuery):
        self.queue[query.id] = query
        logging.info(f"GOALS: added {query} to query")
        logging.info(f"GOALS: {self.queue}")
        
    def do_updates(self):
        if not len(self.queue):
            return
        if (datetime.now() - self.__last_update) < self.__interval:
            return []
        self.__last_update = datetime.now()
        for vi in GoalsGenerator.goals(list(self.queue.values())):
            try:
                del self.queue[vi.id]
                logging.info(vi)
            except KeyError:
                pass

                
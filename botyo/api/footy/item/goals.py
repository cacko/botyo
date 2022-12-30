from typing import Optional, Any
from botyo.goals import Goals as GoalsGenerator, Query as GoalQuery
import logging
from pathlib import Path
from botyo.threesixfive.item.models import GoalEvent
from botyo.core.store import QueueDict

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
    
    __queue: Optional[QueueDict] = None

    @property
    def queue(self) -> QueueDict:
        if not self.__queue:
            self.__queue = QueueDict("goals.queue")
        return self.__queue
    
    def do_monitor(self, query: GoalQuery):
        self.queue[query.id] = query
        logging.debug(f"GOALS: added {query} to query")
        logging.debug(f"GOALS: {self.queue}")
        
    def clean(self):
        try:
            for id in  [x.id for x in self.queue.values() if x.is_expired]:
                del self.queue[id]
        except AssertionError:
            return
        
    def do_updates(self):
        if not len(self.queue):
            return
        self.clean()
        for vi in GoalsGenerator.goals(list(self.queue.values())):
            try:
                vi.rename(GoalsGenerator.output_dir)
                del self.queue[vi.id]
                logging.debug(vi)
            except KeyError:
                pass

                
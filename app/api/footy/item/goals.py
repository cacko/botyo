from typing import Optional, Any
from app.goals import Goals as GoalsGenerator, Query as GoalQuery
from datetime import datetime, timedelta
import logging
from pathlib import Path
from cachable.storage import Storage
import pickle
from app.threesixfive.item.models import (

    GoalEvent
)

class GoalsQueueMeta(type):

    __instances = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds
            )
        return cls.__instances[storage_key]

    def _load(cls, storage_key) -> dict[str, GoalQuery]:
        data = Storage.hgetall(storage_key)
        if not data:
            logging.debug("no data")
            return {}
        items = {k.decode(): pickle.loads(v) for k, v in data.items()}
        return items


class GoalsQueue(dict, metaclass=GoalsQueueMeta):

    __storage_key: str

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        items = __class__._load(storage_key)
        super().__init__(items, *args, **kwds)

    def __setitem__(self, __k, __v) -> None:
        Storage.pipeline().hset(self.__storage_key, __k, pickle.dumps(__v)).persist(
            self.__storage_key
        ).execute()
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        Storage.pipeline().hdel(self.__storage_key, __v).persist(
            self.__storage_key
        ).execute()
        return super().__delitem__(__v)

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
    def queue(self) -> GoalsQueue:
        return GoalsQueue("goals.queue")
    
    def do_monitor(self, query: GoalQuery):
        self.queue[query.id] = query
        logging.info(f"GOALS: added {'/'.join(query.needles)} to query")
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
            except KeyError:
                pass
            logging.info(vi)
                
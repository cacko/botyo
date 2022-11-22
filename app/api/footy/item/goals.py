from typing import Optional, Any
from app.goals import Goals as GoalsGenerator
from datetime import datetime, timedelta

class GoalsMeta(type):
    
    __instance: Optional['Goals'] = None
    
    
    def __call__(cls, *args: Any, **kwds: Any):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, *args, **kwargs)
        return cls.__instance

    def monitor(cls, event_name: str):
        cls().do_monitor(event_name=event_name)
    
    def poll(cls):
        returbn cls().do_updates()


class Goals(object, metaclass=GoalsMeta):
    
    __last_update: datetime = datetime.fromtimestamp(0)
    __interval: timedelta = timedelta(minutes=2)
    __query: list[str] = []
    
    def do_monitor(self, event_name: str):
        self.__query.append(*map(str.lower, event_name.split(" vs ")))
        
    def do_updates(self):
        if not len(self.__query):
            return
        if (datetime.now() - self.__last_update) < self.__interval:
            return []
        self.__last_update = datetime.now()
        for vi in GoalsGenerator.goals(self.__query):
            for m in vi.matches:
                self.__query.remove(m)
            logging.info(vi)
            
                
        
                
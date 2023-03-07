import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .command import CommandExec, CommandMatch
from .config import Config
from .core import AppServer, StoppableThread
from .models import JunkMessage, NoCommand
from .scheduler import Scheduler
from .connection import Context
from .socket.tcp import TCPReceiver


class ServerMeta(type):
    _instance: Optional['Server'] = None
    _cmdMatch: Optional[CommandMatch] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ServerMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def connection(cls, reader, writer):
        cls().onNewConnection(reader, writer)

    @property
    def cmdMatch(cls) -> CommandMatch:
        if not cls._cmdMatch:
            cls._cmdMatch = CommandMatch(
                [*filter(lambda x: len(x.desc) > 0, cls._instance.commands)]
            )
        return cls._cmdMatch


class Server(object, metaclass=ServerMeta):

    commands: list[CommandExec] = []
    executor: ThreadPoolExecutor
    queue: Queue
    scheduler: Scheduler
    config: Config
    groups: list[str] = []
    servers: list[AppServer] = []
    producers = []
    tcpserver: TCPReceiver

    def __init__(self, root_path: Path):
        self.config = Config(root_path)
        self.executor = ThreadPoolExecutor(5)
        self.queue = Queue()

    def register(self, cmd: CommandExec):
        if cmd not in self.commands:
            self.commands.append(cmd)
            logging.debug(f"registering command {cmd.method.value}")
            CommandExec.registered.append(cmd)

    def register_scheduler(self, redis_url):
        scheduler = BackgroundScheduler()
        self.scheduler = Scheduler(scheduler, redis_url)

    def start(self, host, port):
        Scheduler.start()
        Scheduler.remove_all_jobs()
        for srv in self.servers:
            srv.start()
        with TCPReceiver(
            host=host,
            port=int(port),
            queue=self.queue
        ) as self.tcpserver:
            logging.debug(f"Serving requests on {host}:{port}")
            while not self.tcpserver.is_closing:
                try:
                    command, context, t = self.queue.get_nowait()
                    Worker(
                        command=command,
                        context=context,
                        t=t
                    ).start()
                    self.queue.task_done()
                except Empty:
                    pass
                finally:
                    time.sleep(0.2)

    def terminate(self):
        try:
            Scheduler.stop()
        except Exception:
            pass
        for srv in self.servers:
            srv.stop()
        self.tcpserver.terminate()


class Worker(StoppableThread):

    __command: CommandExec
    __context: Context
    __perf_counter: float

    def __init__(self, command: CommandExec, context: Context, t: float, *args, **kwargs):
        self.__command = command
        self.__context = context
        self.__perf_counter = t
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        command = self.__command
        context = self.__context
        t = self.__perf_counter
        logging.debug(f"Consumer got new job")
        try:
            start = time.perf_counter()
            response = command.handler(context)
            t = time.perf_counter() - start
            logging.info(
                f">> executed {command} {t:0.5f} seconds")
            if response:
                context.send(response)
        except (JunkMessage, NoCommand) as e:
            logging.error(e, exc_info=True)
            pass
        except Exception as e:
            logging.error(f"[{command.__class__.__name__}] Error: {e}")
            logging.error(e, exc_info=True)
            pass
        logging.debug(f"CONSUME: {command} done")

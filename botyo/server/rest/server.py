import uvicorn
from botyo.server.core import AppServer
import logging
from corethread import StoppableThread
from fastapi import FastAPI
from .routers import api, ws
from fastapi.middleware.cors import CORSMiddleware
from botyo.core.config import Config


def get_app():
    app = FastAPI()

    origins = [
        "http://localhost:4200",
        "https://geo.cacko.net"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



    app.include_router(api.router)
    app.include_router(ws.router)
    return app

class _APIServer(StoppableThread):

    def __init__(self, *args, **kwargs):
        api_config = Config.api
        server_config = uvicorn.Config(
            app=get_app,
            host=api_config.host, 
            port=api_config.port,
            factory=True
        )
        self.__server = uvicorn.Server(server_config)
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        self.__server.run()

    def stop(self):
        super().stop()
        self.__server.should_exit = True
    


class APIServer(AppServer):
    def __init__(self) -> None:
        worker = _APIServer()
        super().__init__(worker)


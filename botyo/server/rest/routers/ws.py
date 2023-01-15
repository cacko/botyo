from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, HTTPException
)
import logging
from pydantic import BaseModel, Extra
from enum import Enum
from botyo.server.command import CommandExec
from botyo.server.socket.connection import Context
from botyo.core import perftime
from botyo.server.models import RenderResult, ZSONType, EmptyResult
from typing import Optional


class Message(BaseModel, extra=Extra.ignore):
    ztype: ZSONType
    message: str


class Response(BaseModel):
    ztype: str
    method: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    attachment: Optional[str] = None
    plain: Optional[bool] = None


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def process_command(self, msg: Message, client_id: str) -> RenderResult:
        logging.debug(f"process command {msg}")
        command, query = CommandExec.parse(msg.message)
        logging.debug(command)
        context = Context(
            client=client_id,
            query=query,
            group=client_id
        )
        assert isinstance(command, CommandExec)
        with perftime(f"Command {command.method.value}"):
            response = command.handler(context)
            return response


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                logging.debug(f"receive {data}")
                message = Message(**data)
                response = await manager.process_command(message, client_id)
                await websocket.send_json(Response(
                    ztype=ZSONType.RESPONSE.value,
                    message=response.message,
                    method=response.method.value,
                    plain=response.plain
                ).dict())
            except AssertionError as e:
                logging.debug(e)
                response = EmptyResult()
                await websocket.send_json(Response(
                    ztype=ZSONType.RESPONSE.value,
                    message=response.message,
                    plain=response.plain
                ).dict())
    except WebSocketDisconnect:
        manager.disconnect(websocket)

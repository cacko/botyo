from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, HTTPException
)
import logging
from pydantic import BaseModel, Extra, validator
from botyo.server.command import CommandExec
from botyo.server.socket.connection import Context
from botyo.core import perftime
from botyo.server.models import (
    RenderResult,
    ZSONType,
    EmptyResult,
)
from typing import Optional
from base64 import b64encode
from pathlib import Path
from PIL import Image


class WSAttachment(BaseModel):
    contentType: str
    data: str


class Message(BaseModel, extra=Extra.ignore):
    ztype: ZSONType
    id: str
    message: str


class Response(BaseModel):
    ztype: str
    id: str
    method: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    attachment: Optional[WSAttachment] = None
    plain: Optional[bool] = None

    @validator('attachment')
    def static_attachment(cls, attachment: Optional[WSAttachment]):
        try:
            assert attachment
            a_path = Path(attachment.data)
            assert a_path.exists()
            with a_path:
                contentType = attachment.contentType
                if contentType.startswith("image/"):
                    img = Image.open(a_path.as_posix())
                    img.save(a_path.as_posix(), format="webp")
                    contentType = "image/webp"
                return WSAttachment(
                    contentType=contentType,
                    data=b64encode(a_path.read_bytes()).decode()
                ).dict()
        except AssertionError as e:
            logging.error(e)
            return None


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    def process_command(self, msg: Message, client_id: str) -> RenderResult:
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
                response = manager.process_command(message, client_id)
                attachment = None
                if response.attachment:
                    attachment = WSAttachment(
                        contentType=response.attachment.contentType,
                        data=response.attachment.path
                    )
                await websocket.send_json(Response(
                    ztype=ZSONType.RESPONSE.value,
                    id=message.id,
                    message=response.message,
                    method=response.method.value,
                    plain=response.plain,
                    attachment=attachment
                ).dict())
            except Exception as e:
                logging.error(e)
                response = EmptyResult()
                await websocket.send_json(Response(
                    ztype=ZSONType.RESPONSE.value,
                    id="error",
                    error=response.message,
                    plain=response.plain
                ).dict())
    except WebSocketDisconnect:
        manager.disconnect(websocket)

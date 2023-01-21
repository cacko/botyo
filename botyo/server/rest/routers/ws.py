from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, HTTPException
)
import logging
from pydantic import BaseModel, Extra, validator
from botyo.server.command import CommandExec
from botyo.server.connection import Context, Connection
from botyo.core import perftime
from botyo.server.models import (
    RenderResult,
    ZSONType,
    EmptyResult,
    ZSONResponse,
    ZSONRequest
)
from typing import Optional
from base64 import b64encode
from pathlib import Path
from PIL import Image


class WSAttachment(BaseModel):
    contentType: str
    data: str

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


class WSConnection(Connection):
    
    __websocket: WebSocket
    __clientId: str

    def __init__(self, websocket: WebSocket, client_id:str) -> None:
        self.__websocket = websocket
        self.__clientId = client_id

    async def accept(self):
        await self.__websocket.accept()
        __class__.connections[self.__clientId] = self


    async def send_async(self, response: ZSONResponse):
        attachment = None
        if response.attachment:
            attachment = WSAttachment(
                contentType=response.attachment.contentType,
                data=response.attachment.path
            )
        resp = Response(
            ztype=ZSONType.RESPONSE.value,
            id=response.id,
            message=response.message,
            method=response.method.value,
            plain=response.plain,
            attachment=attachment,
            error=response.error
        )
        await self.__websocket.send_json(resp.dict())



class ConnectionManager:

    async def connect(self, websocket: WebSocket, client_id: str):
        await WSConnection(websocket=websocket, client_id=client_id).accept()

    def disconnect(self, client_id):
        WSConnection.remove(client_id)

    async def process_command(self, data: dict, client_id: str) -> RenderResult:
        try:
            msg = ZSONRequest(**data)
            assert isinstance(msg, ZSONRequest)
            logging.debug(f"process command {msg}")
            command, query = CommandExec.parse(msg.query)
            logging.debug(command)
            context = Context(
                client=client_id,
                query=query,
                group=client_id,
                id=msg.id,
                source=msg.source
            )
            assert isinstance(command, CommandExec)
            with perftime(f"Command {command.method.value}"):
                response = command.handler(context)
                await context.send_async(response)
        except Exception as e:
            logging.error(e)
            response = EmptyResult(error=e.__str__)
            await context.send_async(response)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            logging.debug(f"receive {data}")
            await manager.process_command(data, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

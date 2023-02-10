from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)
import logging
from pydantic import BaseModel, Extra, validator, Field
from botyo.server.command import CommandExec
from botyo.server.connection import Context, Connection
from botyo.core import perftime
from botyo.server.models import (
    ZSONType,
    EmptyResult,
    ZSONResponse,
    ZSONRequest,
    CommandDef,
    CoreMethods,
    ZMethod,
)
from typing import Optional
from pathlib import Path
from PIL import Image
from botyo.core.config import Config as app_config
import asyncio
from botyo.firebase.auth import Auth, AuthUser
from corestring import string_hash
import time
from botyo.core.s3 import S3
from botyo.firebase.firestore import FirestoreClient
from datetime import datetime


class WSException(Exception):
    pass


class WSAttachment(BaseModel):
    contentType: str
    url: str


class PingMessage(BaseModel, extra=Extra.ignore):
    ztype: Optional[ZSONType] = None
    id: Optional[str] = None
    client: Optional[str] = None


class PongMessage(BaseModel, extra=Extra.ignore):
    ztype: Optional[ZSONType] = Field(default=ZSONType.PONG)
    id: str


class Response(BaseModel):
    ztype: str
    id: str
    method: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    attachment: Optional[WSAttachment] = None
    plain: Optional[bool] = None
    new_id: Optional[str] = None
    commands: Optional[list[CommandDef]] = None
    icon: Optional[str] = None
    headline: Optional[str] = None
    start_time: Optional[datetime] = None
    status: Optional[str] = None

    @classmethod
    def store_root(cls) -> Path:
        root = Path(app_config.cachable.path) / "ws"
        if not root.exists():
            root.mkdir(parents=True)
        return root

    @validator("attachment")
    def static_attachment(cls, attachment: Optional[WSAttachment]):
        try:
            assert attachment
            a_path = Path(attachment.url)
            hsh = string_hash(a_path.name, str(time.time()))
            a_store_path = cls.store_root() / f"{hsh}{a_path.suffix}"
            assert a_path.exists()
            with a_path:
                contentType = attachment.contentType
                match contentType.split("/")[0]:
                    case "image":
                        img = Image.open(a_path.as_posix())
                        hsh = string_hash(a_path.stem, str(time.time()))
                        a_store_path = cls.store_root() / f"{hsh}.webp"
                        img.save(a_store_path.as_posix(), format="webp")
                        S3.upload(a_store_path, a_store_path.name)
                        a_store_path.unlink(missing_ok=True)
                    case "audio":
                        S3.upload(a_path, a_store_path.name)
                    case "video":
                        S3.upload(a_path, a_store_path.name)
                    case _:
                        raise AssertionError("invalid attachment type")
                return WSAttachment(
                    contentType=contentType, url=f"botyo/{a_store_path.name}"
                ).dict()
        except AssertionError as e:
            logging.error(e)
            return None


router = APIRouter()


class WSConnection(Connection):
    __websocket: WebSocket
    __clientId: str
    __user: Optional[AuthUser] = None

    def __init__(self, websocket: WebSocket, client_id: str) -> None:
        self.__websocket = websocket
        self.__clientId = client_id

    async def accept(self):
        await self.__websocket.accept()
        __class__.connections[self.__clientId] = self

    async def handle_login(self, request: ZSONRequest):
        assert request.query
        self.auth(request.query)
        cmds = ZSONResponse(
            method=CoreMethods.LOGIN,
            commands=CommandExec.definitions,
            client=self.__clientId,
            id=request.id,
        )
        await self.send_async(cmds)

    async def send_error(self, request: ZSONRequest):
        empty = EmptyResult()
        await self.send_async(
            ZSONResponse(
                ztype=ZSONType.RESPONSE,
                id=request.id,
                client=self.__clientId,
                group=self.__clientId,
                error=empty.error_message,
            )
        )

    async def handle_command(self, request: ZSONRequest):
        try:
            assert request.query
            command, query = CommandExec.parse(request.query)
            logging.debug(command)
            context = Context(
                client=self.__clientId,
                query=query,
                group=self.__clientId,
                id=request.id,
                source=request.source,
            )
            assert isinstance(command, CommandExec)
            with perftime(f"Command {command.method.value}"):
                task = asyncio.create_task(command.handler(context))
                result = await task
                logging.warning(result)
                if task.exception():
                    await self.send_error(request=request)
                else:
                    response = task.result()
                    logging.warning(response)
                    await context.send_async(response)
        except AssertionError as e:
            logging.error(e)
            await self.send_error(request=request)
        except Exception as e:
            logging.error(e)
            await self.send_error(request=request)

    def auth(self, token: str):
        self.__user = Auth().verify_token(token)

    def send(self, response: ZSONResponse):
        if not self.__user:
            raise WSException("user is not authenticated")
        try:
            asyncio.run(self.send_async(response))
        except asyncio.CancelledError:
            logging.error(">>>>>>>>>>> DAMBN ERRROR")

    async def send_async(self, response: ZSONResponse):
        if not self.__user:
            raise WSException("user is not authenticated")
        attachment = None
        if response.attachment:
            assert response.attachment.contentType
            assert response.attachment.path
            attachment = WSAttachment(
                contentType=response.attachment.contentType,
                url=response.attachment.path,
            )
        logging.debug(response)
        assert response.id
        resp = Response(
            ztype=ZSONType.RESPONSE,
            id=response.id,
            message=response.message,
            method=response.method,
            plain=response.plain,
            attachment=attachment,
            error=response.error,
            new_id=response.new_id,
            commands=response.commands,
            icon=response.icon,
            headline=response.headline,
            start_time=response.start_time,
            status=response.status
        )
        match response.method:
            case ZMethod.FOOTY_SUBSCRIPTION_UPDATE:
                path = f"subscriptions/{response.id.split(':')[0]}/events"
                FirestoreClient().put(path=path, data=resp.dict())
            case _:
                await self.__websocket.send_json(resp.dict())


class ConnectionManager:
    async def connect(self, websocket: WebSocket, client_id: str):
        connection = WSConnection(websocket=websocket, client_id=client_id)
        await connection.accept()

    def disconnect(self, client_id):
        WSConnection.remove(client_id)

    async def process_command(self, data, client_id):
        try:
            msg = ZSONRequest(**data)
            assert isinstance(msg, ZSONRequest)
            logging.debug(f"process command {msg}")
            assert msg.query
            connection = Connection.client(clientId=client_id)
            assert isinstance(connection, WSConnection)
            match msg.method:
                case CoreMethods.LOGIN:
                    await connection.handle_login(request=msg)
                case _:
                    await connection.handle_command(request=msg)
        except Exception as e:
            logging.exception(e)
            raise WebSocketDisconnect()


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    logging.debug([f"{k} -> {v}" for k, v in websocket.headers.items()])
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("ztype") == ZSONType.PING.value:
                ping = PingMessage(**data)
                assert ping.id
                await websocket.send_json(PongMessage(id=ping.id).dict())
            else:
                logging.debug(f"receive {data}")
                asyncio.create_task(manager.process_command(data, client_id))
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logging.exception(e)

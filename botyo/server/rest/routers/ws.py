from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Cookie,
    Query,
    Depends,
    WebSocketException,
    status,
)
import logging
from pydantic import BaseModel, Extra, validator, Field, ValidationError
from botyo.server.command import CommandExec
from botyo.server.connection import Context, Connection
from botyo.core import perftime
from botyo.server.models import (
    RenderResult,
    ZSONType,
    EmptyResult,
    ZSONResponse,
    ZSONRequest,
    CoreMethods,
)
from typing import Optional, Union
from base64 import b64encode
from pathlib import Path
from PIL import Image
from botyo.core.config import Config as app_config
from fastapi.staticfiles import StaticFiles


class WSAttachment(BaseModel):
    contentType: str
    data: Optional[str] = None
    url: Optional[str] = None


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

    @validator("attachment")
    def static_attachment(cls, attachment: Optional[WSAttachment]):
        try:
            assert attachment
            a_path = Path(attachment.data)
            a_store_path = Path(app_config.cachable.path) / f"ws_{a_path.name}"
            assert a_path.exists()
            with a_path:
                contentType = attachment.contentType
                url = None
                match contentType.split("/")[0]:
                    case "image":
                        img = Image.open(a_path.as_posix())
                        img.save(a_path.as_posix(), format="webp")
                        contentType = "image/webp"
                        return WSAttachment(
                            contentType=contentType,
                            data=b64encode(a_path.read_bytes()).decode(),
                        ).dict()
                    case "audio":
                        url = f"/ws/fp/{a_path.name}"
                        a_path.rename(a_store_path)
                        logging.info(f"copied {a_path} tp {a_store_path}")
                    case "video":
                        url = f"/ws/fp/{a_path.name}"
                        a_path.rename(a_store_path)
                    case _:
                        raise AssertionError("inlvaida attachment type")
                return WSAttachment(contentType=contentType, url=url).dict()

        except AssertionError as e:
            logging.error(e)
            return None


router = APIRouter()
router.mount(
    "/ws/fp",
    StaticFiles(directory=Path(app_config.cachable.path).as_posix()),
    name="static",
)


class WSConnection(Connection):

    __websocket: WebSocket
    __clientId: str

    def __init__(self, websocket: WebSocket, client_id: str) -> None:
        self.__websocket = websocket
        self.__clientId = client_id

    async def accept(self):
        await self.__websocket.accept()
        __class__.connections[self.__clientId] = self
        cmds = ZSONResponse(
            method=CoreMethods.LOGIN,
            commands=CommandExec.definitions,
            client=self.__clientId,
        ).dict()
        await self.__websocket.send_json(cmds)

    async def send_async(self, response: ZSONResponse):
        attachment = None
        if response.attachment:
            attachment = WSAttachment(
                contentType=response.attachment.contentType,
                data=response.attachment.path,
            )
        resp = Response(
            ztype=ZSONType.RESPONSE,
            id=response.id,
            message=response.message,
            method=response.method,
            plain=response.plain,
            attachment=attachment,
            error=response.error,
        )
        await self.__websocket.send_json(resp.dict())


class ConnectionManager:
    async def connect(self, websocket: WebSocket, client_id: str):
        connection = WSConnection(websocket=websocket, client_id=client_id)
        await connection.accept()

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
                source=msg.source,
            )
            assert isinstance(command, CommandExec)
            with perftime(f"Command {command.method.value}"):
                response = command.handler(context)
                await context.send_async(response)
        except Exception as e:
            logging.error(e)
            response = EmptyResult(error=f"{e.__str__}")
            await context.send_async(response)


manager = ConnectionManager()


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Union[str, None] = Cookie(default=None),
    token: Union[str, None] = Query(default=None),
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    # cookie_or_token: str = Depends(get_cookie_or_token),
):
    logging.debug([f"{k} -> {v}" for k, v in websocket.headers.items()])
    await manager.connect(websocket, client_id)
    # logging.debug(f"Session cookie or query token value is: {cookie_or_token}")
    try:
        while True:
            data = await websocket.receive_json()
            logging.debug(f"receive {data}")
            if data.get("ztype") == ZSONType.PING.value:
                ping = PingMessage(**data)
                await websocket.send_json(PongMessage(id=ping.id).dict())
            else:
                await manager.process_command(data, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

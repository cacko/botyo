import logging
from botyo.server.models import RenderResult, Attachment, ZSONResponse
from typing import Optional
from botyo.core.config import Config as app_config
from pydantic import BaseModel

class UnknownClientException(Exception):
    pass


class ConnectionMeta(type):
    connections: dict[str, 'Connection'] = {}

    def client(cls, clientId: str) -> "Connection":
        if clientId not in cls.connections:
            raise UnknownClientException
        return cls.connections[clientId]

    def remove(cls, clientId: str):
        try:
            assert clientId in cls.connections
            del cls.connections[clientId]
        except AssertionError:
            pass


class Connection(object, metaclass=ConnectionMeta):
    def send(self, response: ZSONResponse):
        raise NotImplementedError

    async def send_async(self, response: ZSONResponse):
        raise NotImplementedError


class Context(BaseModel):
    client: Optional[str] = None
    query: Optional[str] = None
    group: Optional[str] = None
    lang: Optional[str] = None
    source: Optional[str] = None
    timezone: Optional[str] = "Europe/London"
    attachment: Optional[Attachment] = None
    id: Optional[str] = None

    @property
    def is_admin(self):
        try:
            superuser = app_config.users.superuser
            is_admin = superuser.evaluate(self.source)
            logging.warn(f"{is_admin} granted super-user")
            return True
        except AssertionError:
            return False

    @property
    def connection(self):
        assert self.client
        return Connection.client(self.client)

    def send(self, result: RenderResult):
        response = ZSONResponse(
            message=result.message,
            attachment=result.attachment,
            client=self.client,
            group=self.group,
            method=result.method,
            plain=bool(result.plain),
            id=self.id,
            icon=result.icon,
            new_id=result.new_id,
        )
        self.connection.send(response=response)

    async def send_async(self, result: RenderResult):
        response = ZSONResponse(
            message=result.message,
            attachment=result.attachment,
            client=self.client,
            group=self.group,
            method=result.method,
            plain=bool(result.plain),
            source=self.source,
            error=result.error,
            id=self.id,
            icon=result.icon,
            new_id=result.new_id,
        )
        await self.connection.send_async(response=response)


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class JsonRpcApiError(Exception):
    pass

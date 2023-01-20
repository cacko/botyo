from botyo.server.models import (
    ZSONResponse,
    RenderResult,
    Attachment
)
import logging
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from typing import Optional


class UnknownClientException(Exception):
    pass


class ConnectionMeta(type):

    connections = {}

    def client(cls, clientId: str) -> 'Connection':
        if clientId not in cls.connections:
            raise UnknownClientException
        return cls.connections[clientId]

    def remove(cls, clientId: str):
        del cls.connections[clientId]



class Connection(object, metaclass=ConnectionMeta):

    def send(self, response: ZSONResponse):
        raise NotImplementedError

    async def send_async(self, response: ZSONResponse):
        raise NotImplementedError



@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Context:

    client: Optional[str] = None
    query: Optional[str] = None
    group: Optional[str] = None
    lang: Optional[str] = None
    source: Optional[str] = None
    timezone: Optional[str] = "Europe/London"
    attachment: Optional[Attachment] = None

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
            plain=result.plain
        )
        self.connection.send(response=response)

    async def send_async(self, result: RenderResult):
        response = ZSONResponse(
            message=result.message,
            attachment=result.attachment,
            client=self.client,
            group=self.group,
            method=result.method,
            plain=result.plain
        )
        await self.connection.send_async(response=response)


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class JsonRpcApiError(Exception):
    pass

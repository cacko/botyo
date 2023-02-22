from pathlib import Path
from socket import socket
from botyo.server.command import CommandExec
from botyo.server.models import (
    ZSONMessage,
    ZSONRequest,
    ZSONResponse,
    ZSONType,
    Method,
    CoreMethods,
)
import logging
from binascii import hexlify, unhexlify
from socketserver import StreamRequestHandler
import tempfile
import time
from botyo.server.connection import (
    Connection,
    Context,
    UnknownClientException
)
from typing import Optional

BYTEORDER = "little"
CHUNKSIZE = 2**8


class SocketConnection(Connection, StreamRequestHandler):

    __clientId: Optional[str] = None
    request: Optional[socket] = None

    @property
    def id(self) -> Optional[str]:
        return self.__clientId

    def setup(self) -> None:
        assert self.request
        self.request.setblocking(True)
        return super().setup()

    def handle(self):
        assert self.request
        logging.info(f"new client connection {self.request.getpeername()}")
        while not self.server.is_closing:  # type: ignore
            try:
                partSize = self.getHeader()
                if not partSize:
                    time.sleep(0.5)
                    continue
                data = self.rfile.read(partSize)
                msg_json = data.decode()
                logging.debug(f">> RECEIVE msg {msg_json}")
                message = ZSONMessage.parse_raw(msg_json)  # type: ignore
                if message.ztype == ZSONType.REQUEST:
                    request = ZSONRequest.parse_raw(msg_json)  # type: ignore
                    if request.method == CoreMethods.LOGIN:
                        if request.client in SocketConnection.connections:
                            logging.debug(
                                f">> Closing old registration {request.client}"
                            )
                            assert request.client
                            connection = SocketConnection.client(request.client)
                            assert isinstance(connection, StreamRequestHandler)
                            connection.request.close()
                            del SocketConnection.connections[request.client]
                        assert request.client
                        self.__clientId = request.client
                        SocketConnection.connections[self.__clientId] = self
                        logging.debug(
                            f">> Client registration {self.__clientId}")
                    elif request.attachment and any(
                        [request.attachment.path, request.attachment.filename
                         ]):
                        if not request.attachment.path:
                            assert request.attachment.filename
                            request.attachment.path = request.attachment.filename
                        download = self.__handleAttachment(
                            Path(request.attachment.path).name)
                        request.attachment.path = download.resolve().as_posix()
                    self.onRequest(message=request)
                    continue
            except (BrokenPipeError):
                return
            except UnknownClientException:
                logging.error(f"!! unknown client {self.__clientId}")
                continue
            except Exception as e:
                logging.exception(e)
                continue
            finally:
                time.sleep(0.5)

    def onRequest(self, message: ZSONRequest):
        try:
            method = message.method
            if method == CoreMethods.LOGIN:
                return self.send(
                    ZSONResponse(method=CoreMethods.LOGIN,
                                 commands=CommandExec.definitions,
                                 client=self.__clientId))
            assert method
            command = CommandExec.triggered(method, message)
            assert command
            context = Context(**message.dict())  # type: ignore
            self.server.queue.put_nowait(  # type: ignore
                (command, context, time.perf_counter()))
            logging.debug(
                f"QUEUE: {command} {self.__clientId} done put in queue")

        except Exception as e:
            logging.exception(e)

    def getHeader(self) -> int:
        try:
            data = self.rfile.read(4)
            assert data
            return int.from_bytes(data, byteorder="little", signed=False)
        except AssertionError:
            return 0

    def __handleAttachment(self, name) -> Path:
        cache_path = Path(tempfile.gettempdir())
        if not cache_path.exists():
            cache_path.mkdir(parents=True)
        p = cache_path / name
        with p.open("wb") as f:
            size = self.getHeader()
            size = size * 2
            logging.debug(f">> ATTACHMENT size={size}")
            while size:
                to_read = CHUNKSIZE if size > CHUNKSIZE else size
                chunk = self.rfile.read(to_read)
                size -= len(chunk)
                f.write(unhexlify(chunk))
            logging.debug(f">> ATTACHMENT saved {p.name}")
        return p

    def _request(self, method: Method):
        req = ZSONRequest(method=method, source="")
        data = req.encode()
        self.wfile.write(
            len(data).to_bytes(4, byteorder="little", signed=False))
        self.wfile.write(data)
        self.wfile.flush()

    def send(self, response: ZSONResponse):
        if response.headline:
            response.message = f"{response.message}\n{response.headline}"
        data = response.encode()
        size = len(data)
        self.wfile.write(size.to_bytes(4, byteorder="little", signed=False))
        self.wfile.write(data)
        self.wfile.flush()
        try:
            assert response.attachment
            assert response.attachment.path
            p = Path(response.attachment.path)
            assert p.exists()
            size = p.stat().st_size
            self.wfile.write(
                size.to_bytes(4, byteorder="little", signed=False), )
            sent = 0
            logging.debug(f">> SEND {size} ATTACHMENT")
            with p.open("rb") as f:
                while data := f.read(CHUNKSIZE):
                    sent += self.wfile.write(hexlify(data))
                    self.wfile.flush()
            logging.debug(f">>>SEND {sent} BYTES")
        except AssertionError:
            pass

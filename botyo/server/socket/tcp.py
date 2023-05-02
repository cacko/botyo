import threading
import socketserver
from botyo.server.socket.connection import SocketConnection
from .base import BaseSocket


class ThreadingTCPServer(
    socketserver.ThreadingMixIn, socketserver.TCPServer
):

    allow_reuse_address: bool = True
    daemon_threads = True

    def __init__(
        self, server_address, handler_class, maxsize=100, timeout=None
    ):
        socketserver.TCPServer.__init__(self, server_address, handler_class)


class TCPServer(threading.Thread, BaseSocket, ThreadingTCPServer):

    def __init__(
        self,
        host,
        port,
        queue,
        request_handler,
        maxsize=0,
        timeout=5,
        daemon=True,
        buffersize=4096,
    ):
        self.queue = queue
        threading.Thread.__init__(self)
        BaseSocket.__init__(self, host, port, buffersize)
        ThreadingTCPServer.__init__(
            self, (host, port), request_handler, maxsize, timeout
        )
        self.daemon = daemon
        self.is_closing = False

    def join(self):
        self.is_closing = True
        self.shutdown()
        return super().join()

    def run(self):
        self.serve_forever()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        print("EXIT")
        self.join()

    def terminate(self):
        for conn in self.connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self.server_close()


class TCPReceiver(TCPServer):

    def __init__(
        self,
        host,
        port,
        queue,
        request_handler=SocketConnection,
        max_queue_size=0,
        timeout=None,
        daemon=True,
        buffersize=4096,
    ):

        super().__init__(
            host,
            port,
            queue,
            request_handler,
            max_queue_size,
            timeout,
            daemon,
            buffersize,
        )
        self.connections = {}

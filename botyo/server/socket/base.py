from queue import Queue


class BaseSocket:
    def __init__(self, ip, port, buffersize):
        self._ip = ip
        self._port = port
        self._buffersize = buffersize

    @property
    def buffersize(self):
        return self._buffersize

    @buffersize.setter
    def buffersize(self, val):
        self._buffersize = val

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def address(self):
        return (self._ip, self._port)

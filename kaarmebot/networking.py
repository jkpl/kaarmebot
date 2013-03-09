import logging
from gevent.socket import socket, AF_INET, SOCK_STREAM


logging.basicConfig()
logger = logging.getLogger(__name__)


class SimpleTCPLineClient:
    def __init__(self, address):
        self.address = address
        self.sock = socket(AF_INET, SOCK_STREAM)
        self._running = False
        self._message_handlers = []
        self._close_handlers = []

    def add_message_handler(self, handler):
        self._message_handlers.append(handler)

    def remove_message_handler(self, handler):
        self._message_handlers.remove(handler)

    def add_close_handler(self, handler):
        self._close_handlers.append(handler)

    def remove_close_handler(self, handler):
        self._close_handlers.remove(handler)

    def close(self):
        if self._running:
            self._running = False
            self.sock.close()
            self._call_close_handlers()

    def is_running(self):
        return self._running

    def send(self, message):
        self.sock.sendall(message + '\r\n')

    def start(self):
        self.sock.connect(self.address)
        stream = self.sock.makefile()
        self._running = True
        while self._running:
            try:
                self._call_message_handlers(stream.readline())
            except IOError:
                self.close()

    def _call_message_handlers(self, line):
        for handler in self._message_handlers:
            handler(line)

    def _call_close_handlers(self):
        for handler in self._close_handlers:
            handler()

import logging
import gevent as g
import gevent.socket as s


logging.basicConfig()
logger = logging.getLogger(__name__)


class SimpleSocketGreenlet(g.Greenlet):
    def __init__(self, address, message_handler, close_handler):
        g.Greenlet.__init__(self)
        self.address = address
        self.message_handler = message_handler
        self.close_handler = close_handler
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.running = False

    def close(self):
        if self.running:
            self.running = False
            self.sock.close()
            self.close_handler()

    def send(self, message):
        self.sock.sendall(message + '\r\n')

    def handle_message(self, message):
        try:
            self.message_handler(message)
        except Exception:
            logger.exception(('Error occurred while attempting '
                              'to handle message.'))

    def _run(self):
        self.sock.connect(self.address)
        stream = self.sock.makefile()
        self.running = True
        try:
            while self.running:
                line = stream.readline()
                self.handle_message(line)
        except Exception:
            logger.exception('Error occurred while reading from socket.')
        finally:
            self.close()

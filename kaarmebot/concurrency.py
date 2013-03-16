import logging
import gevent as g
import gevent.queue as q


logging.basicConfig()
logger = logging.getLogger(__name__)


class ActorInterrupt(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class Actor(g.Greenlet):
    def __init__(self, *args, **kwargs):
        g.Greenlet.__init__(self)
        self.sleep_count = kwargs.get('sleep', 0)
        self.inbox = q.Queue()
        self.running = False
        self.setup(*args, **kwargs)

    def put(self, message):
        self.inbox.put(message)

    def setup(self, *args, **kwargs):
        pass

    def teardown(self):
        pass

    def interrupt(self, message=''):
        raise ActorInterrupt(message)

    def receive(self, message):
        raise NotImplementedError('Receive method isn\'t implemented.')

    def _run(self):
        self.running = True
        try:
            while self.running:
                if not self.inbox.empty():
                    self.receive(self.inbox.get())
                g.sleep(self.sleep_count)
        except ActorInterrupt as e:
            logger.info('Actor receive loop interrupted: %s', e.message)
        except Exception:
            logger.exception('Error occurred in actor receive loop')
        finally:
            self.teardown()
            self.running = False

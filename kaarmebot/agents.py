import logging
import gevent
from gevent.queue import Queue
from gevent.pool import Group


logging.basicConfig()
logger = logging.getLogger(__name__)


class Agent(gevent.Greenlet):
    def __init__(self, workers=1, sleep=0):
        gevent.Greenlet.__init__(self)
        self.sleep_count = sleep
        self._workers = workers
        self._inbox = Queue()
        self.running = False

    def kill(self, exception=gevent.GreenletExit, block=False, timeout=None):
        gevent.Greenlet.kill(self, exception, block, timeout)
        if self.running:
            self.teardown()
            self.running = False

    def put(self, message):
        self._inbox.put(message)

    def setup(self, *args, **kwargs):
        pass

    def teardown(self):
        pass

    def agent_ready(self):
        return True  # ready by default

    def work(self):
        raise NotImplemented()

    def _run(self):
        self.running = True
        jobs = [gevent.spawn(self.work)
                for x in xrange(self._workers)]
        gevent.joinall(jobs)
        self.teardown()
        self.running = False


class ListeningAgent(Agent):
    def receive(self, message):
        raise NotImplemented()

    def work(self):
        while self.running:
            if not self._inbox.empty() and self.agent_ready():
                message = self._inbox.get()
                self.receive(message)
            gevent.sleep(self.sleep_count)


class WorkerAgent(ListeningAgent):
    def worker(self):
        pass

    def work(self):
        jobs = [gevent.spawn(self.worker),
                gevent.spawn(ListeningAgent.work, self)]
        gevent.joinall(jobs)

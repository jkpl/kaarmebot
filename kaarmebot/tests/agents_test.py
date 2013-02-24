import unittest
import gevent
from kaarmebot import agents


class CallbackAgent(agents.Agent):
    def setup(self, callback):
        self.callback = callback

    def teardown(self):
        self.teardown_called = True

    def work(self):
        self.callback()


class KillAgent(agents.Agent):
    def teardown(self):
        self.teardown_called = True

    def work(self):
        while True:
            gevent.sleep(self.sleep_count)
            self.kill()


class ListeningCallbackAgent(agents.ListeningAgent):
    def setup(self, callback):
        self.callback = callback

    def receive(self, message):
        self.callback(message)
        if message == 'kill':
            self.kill()


class WorkerCallbackAgent(agents.WorkerAgent):
    def setup(self, callback):
        self.callback = callback

    def receive(self, message):
        self.callback(message)
        if message == 'kill':
            self.kill()

    def worker(self):
        self.worker_called = True


class TestAgent(unittest.TestCase):
    workers = 4

    def setUp(self):
        self.callback_called = 0

        self.agent = CallbackAgent(workers=self.workers)
        self.agent.setup(self.callback)

        self.agent_kill = KillAgent()
        self.agent_kill.setup()

    def callback(self):
        self.callback_called += 1

    def run_agent(self, agent):
        agent.start()
        agent.join()

    def test_work_is_called_as_many_times_as_workers(self):
        self.run_agent(self.agent)

        self.assertEquals(self.workers, self.callback_called)

    def test_messages_can_be_put_to_agent_inbox(self):
        self.agent.put(1)
        self.agent.put(2)

        self.assertEquals(1, self.agent._inbox.get())
        self.assertEquals(2, self.agent._inbox.get())

    def test_teardown_is_called_after_agent_is_finished(self):
        self.run_agent(self.agent)

        self.assertTrue(self.agent.teardown_called)

    def test_teardown_is_called_after_agent_is_killed(self):
        self.run_agent(self.agent_kill)

        self.assertTrue(self.agent_kill.teardown_called)

    def test_agent_running_state_is_false_after_agent_is_finished(self):
        self.run_agent(self.agent)

        self.assertFalse(self.agent.running)

    def test_agent_running_state_is_false_after_agent_is_killed(self):
        self.run_agent(self.agent_kill)

        self.assertFalse(self.agent_kill)


class TestListeningAgent(unittest.TestCase):
    def setUp(self):
        self.received_messages = []
        self.send_messages = ['one', 'two', 'three', 'kill']
        self.agent = self.setup_agent()

    def setup_agent(self):
        agent = ListeningCallbackAgent()
        agent.setup(self.callback)
        return agent

    def callback(self, message):
        self.received_messages.append(message)

    def run_agent(self):
        self.agent.start()
        self.agent.join()

    def test_receive_gets_the_same_messages_as_what_is_put_to_inbox(self):
        for m in self.send_messages:
            self.agent.put(m)

        self.run_agent()

        self.assertItemsEqual(self.send_messages, self.received_messages)


class TestWorkerAgent(TestListeningAgent):
    def setup_agent(self):
        agent = WorkerCallbackAgent()
        agent.setup(self.callback)
        return agent

    def test_worker_is_called_on_start(self):
        self.agent.put('kill')

        self.run_agent()

        self.assertTrue(self.agent.worker_called)

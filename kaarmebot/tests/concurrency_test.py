import unittest
import kaarmebot.concurrency as c


class StubActor(c.Actor):
    interrupt_string = 'expected interrupt'
    setup_called = False
    teardown_called = False

    def setup(self):
        self.received_messages = []
        self.setup_called = True

    def teardown(self):
        self.teardown_called = True

    def receive(self, message):
        self.received_messages.append(message)
        if message == 'interrupt':
            self.interrupt(self.interrupt_string)
        elif message == 'kill':
            self.kill()


class TestActor(unittest.TestCase):
    first_msg = 'first'
    second_msg = 'second'
    third_msg = 'third'
    kill_msg = 'kill'
    interrupt_msg = 'interrupt'

    def setUp(self):
        self.actor = StubActor()

    def run_actor(self):
        self.actor.start()
        self.actor.join()

    def test_setup_is_called_in_constructor(self):
        self.assertTrue(self.actor.setup_called)

    def test_receive_receives_all_the_put_messages(self):
        messages = (self.first_msg, self.second_msg,
                    self.third_msg, self.interrupt_msg)
        for message in messages:
            self.actor.put(message)

        self.run_actor()

        self.assertItemsEqual(self.actor.received_messages, messages)

    def test_teardown_is_called_on_kill(self):
        self.actor.put(self.kill_msg)

        self.run_actor()

        self.assertTrue(self.actor.teardown_called)

    def test_interrupt_raises_actorinterrupt(self):
        message = 'moi'

        with self.assertRaises(c.ActorInterrupt) as ec:
            self.actor.interrupt(message)

        self.assertEqual(ec.exception.message, message)

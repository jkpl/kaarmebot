import unittest
from kaarmebot import dispatcher


class Message:
    def __init__(self, val):
        self.val = val


class MessageOne(Message):
    pass


class MessageTwo(Message):
    pass


class TestMessageDispatcher(unittest.TestCase):
    def setUp(self):
        self.callback_one_called = 0
        self.callback_two_called = 0
        self.callback_three_called = 0
        self.message1 = MessageOne('some message')
        self.message2 = MessageTwo(True)
        self.message3 = MessageTwo(False)

        self.dispatcher = dispatcher.MessageDispatcher()
        self.dispatcher.add_binding(
            MessageOne, self.predicate_one, self.callback_one)
        self.dispatcher.add_binding(
            MessageTwo, self.predicate_two, self.callback_two)
        self.dispatcher.add_binding(
            MessageOne, self.predicate_one, self.callback_three)

    def predicate_one(self, message):
        return True

    def predicate_two(self, message):
        return message.val

    def callback_one(self, message):
        self.callback_one_called += 1

    def callback_two(self, message):
        self.callback_two_called += 1

    def callback_three(self, message):
        self.callback_three_called += 1

    def test_message_is_dispatched_to_right_binding_class(self):
        self.dispatcher.dispatch(self.message1)

        self.assertEquals(1, self.callback_one_called)
        self.assertEquals(0, self.callback_two_called)
        self.assertEquals(1, self.callback_three_called)

    def test_bindings_can_be_removed(self):
        self.dispatcher.remove_binding(
            MessageOne, self.predicate_one, self.callback_one)
        self.dispatcher.dispatch(self.message1)

        self.assertEquals(0, self.callback_one_called)
        self.assertEquals(0, self.callback_two_called)
        self.assertEquals(1, self.callback_three_called)

    def test_handler_is_only_executed_if_predicate_returns_true(self):
        self.dispatcher.dispatch(self.message3)

        self.assertEquals(0, self.callback_one_called)
        self.assertEquals(0, self.callback_two_called)
        self.assertEquals(0, self.callback_three_called)

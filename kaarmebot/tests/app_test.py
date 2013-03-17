import unittest
import types
import gevent as g
import mockito as m
import utils as u
import kaarmebot.app as app


class DispatcherEngineTest(unittest.TestCase):
    def setUp(self):
        self.pool_size = 4
        self.dispatcher = m.mock()
        m.when(self.dispatcher).get_handlers_for_message(
            m.any()).thenReturn((self.handler_one, self.handler_two))

        self.dispatcher_engine = app.DispatcherEngine(
            self.dispatcher, size=self.pool_size)

    def handler_one(self, message):
        self.handler_one_message = message

    def handler_two(self, message):
        self.handler_two_message = message

    def test_add_binding_calls_dispatcher_add_binding(self):
        routing_class = m.mock()
        predicate = m.mock()
        handler = m.mock()

        self.dispatcher_engine.add_binding(
            routing_class, predicate, handler)

        m.verify(self.dispatcher).add_binding(
            routing_class, predicate, handler)

    def test_remove_binding_calls_dispatcher_remove_binding(self):
        routing_class = m.mock()
        predicate = m.mock()
        handler = m.mock()

        self.dispatcher_engine.remove_binding(
            routing_class, predicate, handler)

        m.verify(self.dispatcher).remove_binding(
            routing_class, predicate, handler)

    def test_dispatch_gets_handlers_from_dispatcher_and_maps_them(self):
        message = 'some message'

        self.dispatcher_engine.dispatch(message)
        self.dispatcher_engine.join()
        g.sleep(0)

        self.assertEquals(self.handler_one_message, message)
        self.assertEquals(self.handler_two_message, message)

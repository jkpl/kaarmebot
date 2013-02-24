import unittest
import gevent
import mockito as m
import types
from kaarmebot import app


class Captor:
    def __init__(self):
        self.args = []
        self.kwargs = []

    def capture(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)


class TestIrcClientAgent(unittest.TestCase):
    address1 = ('somehostname', 1111)
    address2 = ('someotherhostname', 2222)
    irc_message = 'SOME_COOL_MESSAGE_BRO'
    irc_command = 'SOME_COMMAND_YO'

    def setUp(self):
        self.dispatch_agent_mock = m.mock()
        self.dispatcher_mock = m.mock()
        self.irc_client_mock = m.mock()
        self.message_mock = m.mock()

        self.dispatch_agent_mock.dispatcher = self.dispatcher_mock
        self.irc_client_mock.address = self.address1

        self.real_parse_message = app.irc.parse_message
        self.real_any_cmd = app.irc.any_cmd
        m.when(app.irc).parse_message(
            m.any(str)).thenReturn(self.irc_message)
        m.when(app.irc).any_cmd(
            m.any(str)).thenReturn(self.irc_command)

        self.agent = app.IrcClientAgent()
        self.agent.setup(self.dispatch_agent_mock, self.irc_client_mock)

    def tearDown(self):
        app.irc.parse_message = self.real_parse_message
        app.irc.any_cmd = self.real_any_cmd

    def test_add_binding_is_called_on_setup(self):
        m.verify(self.dispatcher_mock).add_binding(
            app.IrcCommandMessage, self.agent.message_matcher,
            self.agent.dispatch_handler)

    def test_message_handler_is_set_on_setup(self):
        m.verify(self.irc_client_mock).add_message_handler(
            self.agent._callback)

    def test_client_close_handler_is_set_on_setup(self):
        m.verify(self.irc_client_mock).add_close_handler(
            self.agent.kill)

    def test_get_address_returns_client_address(self):
        self.irc_client_mock.address = self.address1

        self.assertEquals(self.address1, self.agent.get_address())

    def test_mm_is_true_when_message_target_equals_client_address(self):
        self.message_mock.target = self.address1
        self.irc_client_mock.address = self.address1

        self.assertTrue(self.agent.message_matcher(self.message_mock))

    def test_mm_is_false_when_message_target_not_equals_client_address(self):
        self.message_mock.target = self.address2
        self.irc_client_mock.address = self.address1

        self.assertFalse(self.agent.message_matcher(self.message_mock))

    def test_agent_is_ready_only_when_client_is_running(self):
        m.when(self.irc_client_mock).is_running().thenReturn(True)
        self.assertTrue(self.agent.agent_ready())

        m.when(self.irc_client_mock).is_running().thenReturn(False)
        self.assertFalse(self.agent.agent_ready())

    def test_teardown_closes_client_and_sends_close_message(self):
        captor = Captor()
        self.dispatch_agent_mock.put = captor.capture

        self.agent.teardown()

        msg = captor.args[0][0]
        m.verify(self.irc_client_mock).close()
        self.assertEquals(self.address1, msg.source)
        self.assertEquals('close', msg.contents)

    def test_dispatched_message_has_correct_info(self):
        captor = Captor()
        self.dispatch_agent_mock.put = captor.capture

        self.agent._callback('some uninteresting message')

        msg = captor.args[0][0]
        self.assertEquals(self.address1, msg.source)
        self.assertEquals(self.irc_message, msg.contents)

    def test_receive_sends_messages_to_client(self):
        self.agent.receive('some uninteresting message')
        self.agent.receive(
            app.IrcCommandMessage('some', 'thing', 'whatever'))

        m.verify(self.irc_client_mock, times=2).send(self.irc_command)

    def test_worker_starts_client(self):
        self.agent.worker()

        m.verify(self.irc_client_mock).start()


class TestDispatchAgent(unittest.TestCase):
    dispatch_results = ('one', 'two', 'three', 'four')

    def setUp(self):
        self.dispatcher_mock = m.mock()

        m.when(self.dispatcher_mock).dispatch(
            m.any(str)).thenReturn(self.dispatch_results)

        self.agent = app.DispatchAgent()
        self.agent.setup(self.dispatcher_mock)

    def test_results_are_queued_after_dispatched(self):
        messages = []

        self.agent.receive('something uninteresting')

        while not self.agent._inbox.empty():
            messages.append(self.agent._inbox.get())

        self.assertItemsEqual(self.dispatch_results, messages)


class TestControlAgent(unittest.TestCase):
    target = 'TARGET'
    source = 'SOURCE'
    command = 'COMMAND'
    test_string = 'something'

    def setUp(self):
        self.group_mock = m.mock()
        self.irc_client_mock = m.mock()
        self.dispatch_agent_mock = m.mock()
        self.dispatcher_mock = m.mock()

        self.agent_captor = Captor()
        self.group_mock.start = self.agent_captor.capture

        self.message_captor = Captor()
        self.dispatch_agent_mock.put = self.message_captor.capture
        self.dispatch_agent_mock.dispatcher = self.dispatcher_mock

        self.real_pong = app.irc.pong
        self.real_join = app.irc.join

        self.server_address = ('some_hostname', 1111)
        self.server_settings = {
            'username': 'USER_NAME',
            'real_name': 'REAL_NAME',
            'password': 'PASSWORD',
            'nick': 'NICK',
            'channels': ('#chan1', '#chan2')
        }
        self.servers = {self.server_address: self.server_settings}

        self.agent = app.ControlAgent()
        self.agent.setup(self.servers, self.dispatch_agent_mock,
                         self.group_mock, self.client_generator)

    def tearDown(self):
        app.irc.pong = self.real_pong
        app.irc.join = self.real_join

    def client_generator(self, address):
        self.irc_client_mock.address = address
        return self.irc_client_mock

    def test_send_command_dispatches_commands(self):
        self.agent.send_command(self.target, self.command)

        message = self.message_captor.args[0][0]
        self.assertTrue(isinstance(message, app.IrcCommandMessage))
        self.assertEquals(self.target, message.target)
        self.assertEquals(self.command, message.contents)

    def test_handle_ping_sends_correct_pong_message(self):
        ok_value = 'OK'
        irc_message = app.IrcClientMessage(
            self.source, self.target,
            app.irc.IrcMessage(None, 'PING', None, self.test_string, None))
        m.when(app.irc).pong(self.test_string).thenReturn(ok_value)

        self.agent.handle_ping(irc_message)

        message = self.message_captor.args[0][0]
        self.assertEquals(ok_value, message.contents)
        self.assertEquals(self.source, message.target)

    def test_handle_connected_sends_proper_join_commands(self):
        ok_value = 'OK'
        irc_message = app.IrcClientMessage(
            self.server_address, self.target,
            app.irc.IrcMessage(None, '001', None, None, None))
        m.when(app.irc).join(
            self.server_settings['channels']).thenReturn(ok_value)

        self.agent.handle_connected(irc_message)

        message = self.message_captor.args[0][0]
        self.assertEquals(ok_value, message.contents)
        self.assertEquals(self.server_address, message.target)

    def test_handle_connected_does_nothing_when_source_is_unknown(self):
        irc_message = app.IrcClientMessage(
            self.source, self.target,
            app.irc.IrcMessage(None, '001', None, None, None))

        self.agent.handle_connected(irc_message)

        self.assertEquals(0, len(self.message_captor.args))

    def test_irc_agent_close_restarts_connection(self):
        irc_agent_message = app.IrcAgentMessage(
            self.server_address, None, 'close')

        self.agent.handle_irc_agent_close(irc_agent_message)

        agent = self.agent_captor.args[0][0]
        messages = self.message_captor.args
        self.assertEquals(self.server_address, agent.get_address())
        self.assertEquals(self.dispatch_agent_mock, agent.dispatch_agent)
        self.assertEquals(self.server_address, irc_agent_message.source)
        self.assertEquals(3, len(messages))

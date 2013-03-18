import unittest
import types
import mockito as m
import utils as u
import kaarmebot.applogic as al


class CommonTestCase(unittest.TestCase):
    any_cmd_output = 'any_cmd'
    message_parser_output = 'message_parser'

    def message_parser(self, message):
        return self.message_parser_output

    def setup_module(self):
        self.dispatcher = m.mock()
        self.provided_client = m.mock()
        self.logger = m.mock()
        self.concurrency_manager = m.mock()
        self.plugin_manager = m.mock()

        self.client_provider = u.FakeProvider(self.provided_client)
        self.dispatch_captor = u.ArgumentCaptor()
        self.bindings_captor = u.ArgumentCaptor()

        self.setup_mock_rules_and_captors()

    def setup_mock_rules_and_captors(self):
        self.dispatcher.dispatch = self.dispatch_captor.capture
        self.dispatcher.add_binding = self.bindings_captor.capture

    def verify_no_exceptions_logged(self):
        m.verifyNoMoreInteractions(self.logger)


class ClientTest(CommonTestCase):
    name = 'some name'
    address = 'some address'

    def setUp(self):
        self.setup_module()
        self.client = al.Client(
            name=self.name,
            address=self.address,
            message_parser=self.message_parser,
            dispatcher=self.dispatcher,
            client_provider=self.client_provider)

        self.client_provider_arguments = self.client_provider.last_arguments
        self.binding_arguments = self.bindings_captor.last_arguments
        self.message_handler = self.client_provider_arguments[1]
        self.close_handler = self.client_provider_arguments[2]
        self.message_matcher = self.binding_arguments[1]
        self.command_handler = self.binding_arguments[2]

    def test_client_is_created_using_client_provider_on_construct(self):
        self.assertEquals(self.provided_client, self.client.client)

    def test_address_is_passed_to_client_provider_on_construct(self):
        self.assertIn(self.address, self.client_provider_arguments)

    def test_command_bindings_are_set_to_dispatcher_on_construct(self):
        self.assertIn(al.Command, self.binding_arguments)

    def test_client_started_message_is_dispatcher_on_construct(self):
        message = self.dispatch_captor.last_arguments[0]

        self.assertEquals(message.source, self.name)
        self.assertEquals(message.contents, 'started')

    def test_command_handler_passes_each_command_to_client(self):
        command1 = 'some command'
        command2 = 'other command'
        message = al.Command(None, None, (command1, command2))

        self.command_handler(message)

        m.verify(self.provided_client).put(command1)
        m.verify(self.provided_client).put(command2)

    def test_message_matcher_gives_true_only_when_message_target_is_name(self):
        valid_message = al.Message(None, self.name, None)
        invalid_message = al.Message(None, self.name + '...', None)

        self.assertTrue(self.message_matcher(valid_message))
        self.assertFalse(self.message_matcher(invalid_message))

    def test_message_handler_gives_parsed_message_to_dispatcher_engine(self):
        message = 'some message'

        self.message_handler(message)

        dispatched_message = self.dispatch_captor.last_arguments[0]

        self.assert_message_matches(dispatched_message, al.ClientMessage,
                                    self.message_parser_output)

    def assert_message_matches(self, message, expected_class,
                               expected_contents):
        self.assertEquals(message.__class__, expected_class)
        self.assertEquals(message.source, self.name)
        self.assertEquals(message.contents, expected_contents)

    def test_client_close_handler_behaves_as_expected(self):
        self.close_handler()
        dispatched_message = self.dispatch_captor.last_arguments.args[0]

        m.verify(self.dispatcher).remove_binding(
            al.Command, m.any(types.FunctionType), m.any(types.FunctionType))
        self.assert_message_matches(
            dispatched_message, al.ClientStatusMessage, 'close')


class PluginStub(object):
    result = 'pluginstubresult'

    def __init__(self, request):
        self.request = request

    def handler(self):
        return self.result


class PluginHandlerTest(CommonTestCase):
    name = 'some_name'
    executable_result = 'some result'
    source = 'some source'
    contents = 'some contents'
    message = al.Message(source, None, contents)

    def executable(self, request):
        self.request = request
        return self.executable_result

    def setUp(self):
        self.setup_module()
        self.settings = {'something': 'whatever'}
        self.source_settings = 'source settings'
        self.app_settings = {
            'servers': {self.source: self.source_settings}
        }
        self.plugin_handler = self.create_plugin_handler(self.executable)

    def create_plugin_handler(self, executable):
        return al.PluginHandler(
            self.name, executable, self.settings,
            self.app_settings, self.dispatcher, self.logger)

    def assert_message_matches_command(self, message, contents):
        self.assertEquals(message.__class__, al.Command)
        self.assertEquals(message.target, self.source)
        self.assertEquals(message.contents, contents)

    def test_calling_handler_passes_right_request_to_executable(self):
        self.plugin_handler(self.message)

        self.verify_no_exceptions_logged()

        self.assertEquals(self.request.message, self.contents)
        self.assertEquals(self.request.source, self.source)
        self.assertEquals(self.request.source_settings, self.source_settings)
        self.assertEquals(self.request.app_settings, self.app_settings)
        self.assertEquals(self.request.plugin_settings, self.settings)

    def test_calling_handler_passes_executable_result_to_dispatcher(self):
        self.plugin_handler(self.message)

        self.verify_no_exceptions_logged()
        message = self.dispatch_captor.last_arguments[0]

        self.assert_message_matches_command(message, self.executable_result)

    def test_calling_executable_with_attr_setting_calls_the_attr(self):
        self.settings['attr'] = 'handler'
        plugin_handler = self.create_plugin_handler(PluginStub)

        plugin_handler(self.message)

        self.verify_no_exceptions_logged()

        message = self.dispatch_captor.last_arguments[0]

        self.assert_message_matches_command(message, PluginStub.result)


class ConnectionStarterTest(CommonTestCase):
    def setUp(self):
        self.setup_module()

        self.server1_key = 'server1_key'
        self.server1_conf = 'server1_conf'
        self.server2_key = 'server2_key'
        self.server2_conf = 'server2_conf'
        self.servers = {self.server1_key: self.server1_conf,
                        self.server2_key: self.server2_conf}

        self.connection_starter = al.ConnectionStarter(
            self.servers, self.concurrency_manager, self.client_provider)

    def test_connections_are_started_for_known_servers(self):
        message = al.Message(self.server1_key, None, None)
        self.connection_starter(message)

        m.verify(self.concurrency_manager).start(self.provided_client)
        arguments = self.client_provider.last_arguments
        self.assertIn(self.server1_key, arguments)
        self.assertIn(self.server1_conf, arguments)

    def test_connections_are_not_started_for_unknown_servers(self):
        message = al.Message(self.server1_key + '!!!', None, None)
        self.connection_starter(message)

        m.verify(self.concurrency_manager, m.never).start(m.any())

    def test_start_all_connections_starts_all_connections(self):
        self.connection_starter.start_all_connections()

        m.verify(self.concurrency_manager, times=2).start(self.provided_client)


class BotAppTest(CommonTestCase):
    def setUp(self):
        self.setup_module()

        self.server1_key = 'server1_key'
        self.server1_address = 'someaddress1'
        self.server1_conf = {'address': self.server1_address}
        self.server2_key = 'server2_key'
        self.server2_address = 'someaddress2'
        self.server2_conf = {'address': self.server2_address}
        self.servers = {self.server1_key: self.server1_conf,
                        self.server2_key: self.server2_conf}
        self.app_settings = {'servers': self.servers}

        self.botapp = al.BotApp(
            dispatcher=self.dispatcher,
            concurrency_manager=self.concurrency_manager,
            client_provider=self.client_provider,
            plugin_manager=self.plugin_manager,
            message_parser=self.message_parser,
            logger=self.logger,
            app_settings=self.app_settings)

    def test_close_handling_binding_is_set_on_construct(self):
        arguments = self.bindings_captor.last_arguments

        self.assertEquals(arguments[0], al.ClientStatusMessage)
        self.assertIsInstance(arguments[1], types.FunctionType)
        self.assertIsNotNone(arguments[2])

    def test_close_message_matcher_matches_known_client_closing_messages(self):
        first_valid_message = al.Message(self.server1_key, None, 'close')
        first_invalid_message = al.Message(self.server1_key, None, 'waddap')
        second_invalid_message = al.Message('fjklfdajlk', None, 'close')
        third_invalid_message = al.Message('fjkdlfjk', None, 'wooot')

        matcher = self.bindings_captor.last_arguments[1]

        self.assertTrue(matcher(first_valid_message))
        self.assertFalse(matcher(first_invalid_message))
        self.assertFalse(matcher(second_invalid_message))
        self.assertFalse(matcher(third_invalid_message))

    def test_close_message_handler_is_a_proper_connection_starter(self):
        handler = self.bindings_captor.last_arguments[2]

        self.assertIsInstance(handler, al.ConnectionStarter)
        self.assertEquals(handler.servers, self.servers)
        self.assertEquals(handler.concurrency_manager,
                          self.concurrency_manager)
        self.assertEquals(handler.client_provider,
                          self.botapp.wrapped_client_provider)

    def test_wrapped_client_provider_creates_proper_clients(self):
        client = self.botapp.wrapped_client_provider(
            self.server1_key, self.server1_conf)

        client_provider_arguments = self.client_provider.last_arguments
        binding_arguments = self.bindings_captor.last_arguments

        self.assertEquals(client, self.provided_client)
        self.assertEquals(client_provider_arguments[0], self.server1_address)
        self.assertEquals(binding_arguments[0], al.Command)
        self.assertIsInstance(binding_arguments[1], types.FunctionType)
        self.assertIsInstance(binding_arguments[2], types.FunctionType)

    def test_start_starts_all_connections_and_joins_with_cmanager(self):
        self.botapp.start()

        m.verify(self.concurrency_manager, times=2).start(self.provided_client)
        m.verify(self.concurrency_manager).join()

    def test_plugin_configurer_is_set_to_plugin_manager_on_construct(self):
        self.assertEquals(self.botapp.plugin_configurer,
                          self.plugin_manager.plugin_configurer)

    def test_plugin_configurer_creates_plugin_handler(self):
        base_handler = lambda x: 'base_handler'
        name = 'some name'
        some_key = 'some_key'
        settings = {some_key: 4}

        handler, settings = self.plugin_manager.plugin_configurer(
            base_handler, name, settings)

        self.assertIsInstance(handler, al.PluginHandler)
        self.assertEquals(handler.name, name)
        self.assertEquals(handler.executable, base_handler)
        self.assertEquals(handler.dispatcher, self.dispatcher)
        self.assertEquals(handler.logger, self.logger)
        self.assertIn(some_key, handler.settings)
        self.assertIn('routing_class', handler.settings)
        self.assertEquals(handler.app_settings, self.app_settings)

    def test_add_plugin_passes_call_to_plugin_manager(self):
        base_handler = lambda x: 'base_handler'
        name = 'some name'
        some_key = 'some_key'
        settings = {some_key: 4}

        self.botapp.add_plugin(base_handler, name, **settings)

        m.verify(self.plugin_manager).add_plugin(
            base_handler, name, some_key=4)

    def test_add_binding_adds_correct_binding_via_plugin_manager(self):
        predicate = lambda x: 'predicate'
        name = 'some_name'
        value = 'avalue'
        settings = {'akey': value}

        self.botapp.add_binding(predicate, name, **settings)

        m.verify(self.plugin_manager).add_binding(predicate, name, akey=value)

    def test_scan_calls_plugin_manager_scan(self):
        module = m.mock()

        self.botapp.scan(module)

        m.verify(self.plugin_manager).scan(module)

import collections as c


PluginRequest = c.namedtuple(
    'PluginRequest', ['message', 'source', 'source_settings',
                      'app_settings', 'plugin_settings'])
Message = c.namedtuple(
    'Message', ['source', 'target', 'contents'])


class ClientMessage(Message):
    pass


class ClientStatusMessage(Message):
    pass


class Command(Message):
    pass


class BotApp(object):
    def __init__(self, network_client_provider, dispatcher, concurrency_manager,
                 message_parser, plugin_manager, logger, app_settings):
        self.network_client_provider = network_client_provider
        self.dispatcher = dispatcher
        self.concurrency_manager = concurrency_manager
        self.message_parser = message_parser
        self.plugin_manager = plugin_manager
        self.logger = logger
        self.app_settings = app_settings

        self.plugin_manager.plugin_configurer = self.plugin_configurer
        self.client_provider = self.create_client_provider()
        self.connection_starter = self.create_connection_starter()

        self.dispatcher.add_binding(
            ClientStatusMessage,
            self.create_close_message_matcher(),
            self.connection_starter)

    def create_close_message_matcher(self):
        servers = self.app_settings['servers']

        def is_close_message(message):
            return (message.contents == 'close' and message.source in servers)

        return is_close_message

    def create_connection_starter(self):
        return ConnectionStarter(
            servers=self.app_settings['servers'],
            client_provider=self.client_provider,
            concurrency_manager=self.concurrency_manager)

    def create_client_provider(self):
        message_parser = self.message_parser
        dispatcher = self.dispatcher
        network_client_provider = self.network_client_provider

        def create_client(name, server_conf):
            client = Client(
                name=name,
                address=server_conf['address'],
                message_parser=message_parser,
                dispatcher=dispatcher,
                network_client_provider=network_client_provider)
            return client.client

        return create_client

    def create_plugin_handler(self, handler, name, settings):
        return PluginHandler(
            name=name,
            executable=handler,
            settings=settings,
            app_settings=self.app_settings,
            dispatcher=self.dispatcher,
            logger=self.logger)

    def start(self):
        self.connection_starter.start_all_connections()
        self.concurrency_manager.join()

    def plugin_configurer(self, handler, name, settings):
        if not settings.get('routing_class'):
            settings['routing_class'] = ClientMessage
        plugin_handler = self.create_plugin_handler(handler, name, settings)
        return (plugin_handler, settings)

    def add_plugin(self, handler, name, **settings):
        self.plugin_manager.add_plugin(handler, name, **settings)

    def add_binding(self, predicate, name, **moresettings):
        self.plugin_manager.add_binding(predicate, name, **moresettings)

    def scan(self, module):
        self.plugin_manager.scan(module)


class ConnectionStarter(object):
    def __init__(self, servers, concurrency_manager, client_provider):
        self.servers = servers
        self.concurrency_manager = concurrency_manager
        self.client_provider = client_provider

    def __call__(self, message):
        name = message.source
        self.start_connection(name)

    def start_connection(self, name):
        server_conf = self.servers.get(name)
        if server_conf:
            self.start_connection_for_conf(name, server_conf)

    def start_all_connections(self):
        for name, server_conf in self.servers.iteritems():
            self.start_connection_for_conf(name, server_conf)

    def start_connection_for_conf(self, name, server_conf):
        client = self.client_provider(name, server_conf)
        self.concurrency_manager.start(client)


class Client(object):
    def __init__(self, name, address, message_parser, dispatcher,
                 network_client_provider):
        self.name = name
        self.message_parser = message_parser
        self.dispatcher = dispatcher

        message_handler = get_attribute_as_function(self, 'handle_message')
        close_handler = get_attribute_as_function(self, 'handle_close')
        command_handler = get_attribute_as_function(self, 'handle_command')
        message_matcher = message_matcher_generator(name)

        self.bindings = (
            (Command, message_matcher, command_handler),
        )

        self.client = network_client_provider(address, message_handler, close_handler)
        add_bindings_to_dispatcher(self.bindings, self.dispatcher)
        self.dispatcher.dispatch(
            ClientStatusMessage(self.name, None, 'started'))

    def handle_close(self):
        remove_bindings_from_dispatcher(self.bindings, self.dispatcher)
        close_message = ClientStatusMessage(self.name, None, 'close')
        self.dispatcher.dispatch(close_message)

    def handle_message(self, message):
        client_message = ClientMessage(
            self.name, None,
            self.message_parser(message))
        self.dispatcher.dispatch(client_message)

    def handle_command(self, message):
        commands = message.contents
        if not type(commands) in (tuple, list):
            commands = (commands,)
        for command in commands:
            self.client.put(command)


class PluginHandler(object):
    def __init__(self, name, executable, settings,
                 app_settings, dispatcher, logger):
        self.name = name
        self.executable = executable
        self.settings = settings
        self.app_settings = app_settings
        self.dispatcher = dispatcher
        self.logger = logger
        self.attr = settings.get('attr')

    def __call__(self, message):
        try:
            self.handle(message)
        except Exception:
            self.logger.exception(
                'Error occurred while executing handler: %s',
                self.name)

    def handle(self, message):
        contents = getattr(message, 'contents', message)
        source = getattr(message, 'source', '')
        result = self._execute(contents, source)
        self.dispatcher.dispatch(
            Command(None, message.source, result))

    def _execute(self, contents, source):
        request = PluginRequest(
            contents, source,
            self.app_settings['servers'].get(source),
            self.app_settings, self.settings)
        result = self.executable(request)
        if self.attr:
            result = getattr(result, self.attr)()
        return result


## Helpers
def add_bindings_to_dispatcher(bindings, dispatcher):
    for binding in bindings:
        c, p, h = binding
        dispatcher.add_binding(c, p, h)


def remove_bindings_from_dispatcher(bindings, dispatcher):
    for binding in bindings:
        c, p, h = binding
        dispatcher.remove_binding(c, p, h)


def message_matcher_generator(name):
    def message_matcher(message):
        return message.target == name

    return message_matcher


def get_attribute_as_function(obj, attr):
    callable_attribute = getattr(obj, attr)

    def inner(*args, **kwargs):
        return callable_attribute(*args, **kwargs)

    return inner

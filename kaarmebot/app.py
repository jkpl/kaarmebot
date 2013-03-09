import venusian
import logging
import irc
import agents
import predicates as p
import dispatcher as d
import networking as n
from gevent.pool import Group


logging.basicConfig()
logger = logging.getLogger(__name__)


def plugin_config(**settings):
    def decorator(wrapped):
        sets = settings.copy()

        def callback(scanner, name, ob):
            if sets.get('name') is None:
                sets['name'] = name
            scanner.add_plugin(ob, **sets)

        info = venusian.attach(wrapped, callback, category='plugins')
        if info.scope == 'class' and sets.get('attr') is None:
            sets['attr'] = wrapped.__name__
        return wrapped
    return decorator


class BotApp:
    def __init__(self, bot_settings):
        self.plugins = {}
        self.bot_settings = bot_settings
        self.dispatcher = d.MessageDispatcher()
        self.dispatch_agent = DispatchAgent()
        self.dispatch_agent.setup(self.dispatcher)
        self.agent_group = Group()
        self.control_agent = ControlAgent()
        self.control_agent.setup(
            self.bot_settings['servers'], self.dispatch_agent,
            self.agent_group, simplelineclient_generator)
        self._scanner = venusian.Scanner(add_plugin=self.add_plugin)

    def start(self):
        self.agent_group.start(self.dispatch_agent)
        self.agent_group.start(self.control_agent)
        self.control_agent.start_connections()
        self.agent_group.join()

    def add_plugin(self, handler, name, **settings):
        nid = settings.get('name', name)
        self.plugins[nid] = (handler, settings)

    def add_binding(self, predicate, name, **moresettings):
        plugin_handler, settings = self.plugins[name]
        settings.update(moresettings)
        self.dispatcher.add_binding(
            IrcClientMessage, predicate,
            plugin_handler_wrapper(plugin_handler, settings))

    def scan(self, module):
        self._scanner.scan(module)


def simplelineclient_generator(address):
    return n.SimpleTCPLineClient(address)


def plugin_handler_wrapper(plugin_handler, settings):
    attr = settings.get('attr')
    def handler(message):
        contents = getattr(message, 'contents', message)
        result = plugin_handler(contents, settings)
        if attr:
            result = getattr(result, attr)()
        return IrcCommandMessage(None, message.source, result)
    return handler


class IrcClientMessage(d.Message):
    pass


class IrcAgentMessage(d.Message):
    pass


class IrcCommandMessage(d.Message):
    pass


class IrcClientAgent(agents.WorkerAgent):
    def setup(self, dispatch_agent, irc_client):
        self.dispatch_agent = dispatch_agent
        self.dispatch_agent.dispatcher.add_binding(
            IrcCommandMessage, self.message_matcher, self.dispatch_handler)
        self._irc_client = irc_client
        self._irc_client.add_message_handler(self._callback)
        self._irc_client.add_close_handler(self.kill)

    def message_matcher(self, message):
        return message.target == self.get_address()

    def dispatch_handler(self, message):
        self.put(message)

    def worker(self):
        self._irc_client.start()

    def agent_ready(self):
        return self._irc_client.is_running()

    def receive(self, message):
        if isinstance(message, IrcCommandMessage):
            command = irc.any_cmd(message.contents)
        else:
            command = irc.any_cmd(message)
        self._irc_client.send(command)

    def teardown(self):
        self._irc_client.close()
        self.dispatch_agent.put(
            IrcAgentMessage(self.get_address(), None, 'close'))

    def get_address(self):
        return self._irc_client.address

    def _callback(self, message):
        try:
            address = self.get_address()
            ircmsg = irc.parse_message(message)
            self.dispatch_agent.put(IrcClientMessage(address, None, ircmsg))
        except Exception as e:
            logger.exception(("Error occurred when reading "
                              "message from client."))


class DispatchAgent(agents.ListeningAgent):
    def setup(self, dispatcher):
        self.dispatcher = dispatcher

    def receive(self, message):
        try:
            for result in self.dispatcher.dispatch(message):
                self.put(result)
        except Exception as e:
            logger.exception("Error while trying to dispatch message.")


class ControlAgent(agents.ListeningAgent):
    def setup(self, servers, dispatch_agent, agent_group, client_generator):
        self.servers = servers
        self.dispatch_agent = dispatch_agent
        self.agent_group = agent_group
        self.client_generator = client_generator

        self.dispatch_agent.dispatcher.add_bindings(
            (IrcAgentMessage, lambda message: message.contents == 'close',
             self.handle_irc_agent_close),
            (IrcClientMessage, p.Ping, self.handle_ping),
            (IrcClientMessage, p.Connected, self.handle_connected),
        )

    def send_command(self, target, command):
        self.dispatch_agent.put(IrcCommandMessage(None, target, command))

    def handle_irc_agent_close(self, message):
        server_conf = self.servers.get(message.source)
        if server_conf:
            self.start_connection(message.source, server_conf)

    def handle_ping(self, message):
        target = message.contents.body
        self.send_command(message.source, irc.pong(target))

    def handle_connected(self, message):
        server = self.servers.get(message.source, {})
        channels = server.get('channels')
        if channels:
            self.send_command(message.source, irc.join(channels))

    def start_connections(self):
        for address, settings in self.servers.iteritems():
            self.start_connection(address, settings)

    def start_connection(self, address, server_conf):
        irc_agent = IrcClientAgent()
        irc_client = self.client_generator(address)
        irc_agent.setup(self.dispatch_agent, irc_client)
        self.connection_login(address, server_conf)
        self.agent_group.start(irc_agent)

    def connection_login(self, address, server_conf):
        self.send_command(
            address, irc.user(server_conf['username'],
                              server_conf.get('usermode', 8),
                              server_conf['real_name']))
        if server_conf.get('password'):
            self.send_command(
                address,irc.password(server_conf.get('password')))
        self.send_command(address, irc.nick(server_conf['nick']))

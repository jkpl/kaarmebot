import logging
import gevent as g
import predicates as pr
import dispatcher as d
import networking as n
import concurrency as c
import applogic as al
import plugin as pl
import gevent.pool as pool
import builtin_plugins
import irc


logging.basicConfig()
logger = logging.getLogger(__name__)


class DefaultKaarmeBotApp(al.BotApp):
    def __init__(self, app_settings):
        dispatcher = DispatcherEngine(
            d.MessageDispatcher(),
            size=app_settings.get('dispatcher_pool_size', 100))
        super(DefaultKaarmeBotApp, self).__init__(
            client_provider=ClientGreenlet,
            dispatcher=dispatcher,
            concurrency_manager=pool.Group(),
            message_parser=irc.parse_message,
            plugin_manager=pl.PluginManager(dispatcher),
            logger=logger,
            app_settings=app_settings)


class KaarmeBotApp(DefaultKaarmeBotApp):
    def __init__(self, app_settings):
        super(KaarmeBotApp, self).__init__(app_settings)
        self.scan(builtin_plugins)
        self.add_binding(pr.Ping, 'builtin_ping')
        self.add_binding(pr.Connected, 'builtin_after_connect_join')
        self.add_binding(pr.ClientStarted, 'builtin_init_connection')


class DispatcherEngine(pool.Pool):
    def __init__(self, dispatcher, size=None, greenlet_class=None):
        pool.Pool.__init__(self, size, greenlet_class)
        self.dispatcher = dispatcher

    def add_binding(self, *args, **kwargs):
        self.dispatcher.add_binding(*args, **kwargs)

    def remove_binding(self, *args, **kwargs):
        self.dispatcher.remove_binding(*args, **kwargs)

    def dispatch(self, message):
        def run_handler(handler):
            handler(message)

        handlers = self.dispatcher.get_handlers_for_message(message)
        self.map_async(run_handler, handlers)


class ClientGreenlet(g.Greenlet):
    def __init__(self, address, message_handler, close_handler):
        g.Greenlet.__init__(self)
        self.client = n.SimpleTCPLineClient(
            address, message_handler, close_handler)
        self.message_sender = ClientSender(self.client)

    def put(self, message):
        self.message_sender.put(message)

    def __str__(self):
        return repr(self.client.address)

    def _run(self):
        self.client.link(self.message_sender)
        try:
            self.client.start()
            self.message_sender.start()
            g.joinall([self.client, self.message_sender])
        except Exception:
            logger.exception('Error occurred in client (%s).',
                             self.client.address)
        finally:
            self.client.close()


class ClientSender(c.Actor):
    def setup(self, client):
        self.client = client

    def actor_ready(self):
        return self.client.running

    def receive(self, message):
        msg = message
        try:
            if isinstance(message, al.Message):
                msg = message.contents
            if msg:
                self.send_commands(msg)
        except IOError:
            logger.exception('Error occurred while sending message.')

    def send_commands(self, commands):
        command_list = commands
        if not type(command_list) in (tuple, list):
            command_list = (command_list,)
        for command in command_list:
            self.client.send(command)

    def __str__(self):
        return repr(self.client.address)

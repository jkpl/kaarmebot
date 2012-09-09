import types
import venusian
import gevent
import logging
from gevent.queue import Queue
from botcore import BotCore
from dispatcher import MessageDispatcher


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
    def __init__(self, channels, servers, nickname, real_name, workers=4,
                 plugin_settings=None):
        self.plugins = {}
        self._workernum = workers
        self._queue = Queue()
        self.dispatcher = MessageDispatcher(plugin_settings,
                                            irc_message_filter)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self.queue_message)
        self._scanner = venusian.Scanner(add_plugin=self.add_plugin)

    def add_binding(self, pattern, name, **moresettings):
        handler, settings = self.plugins[name]
        settings.update(moresettings)
        self.dispatcher.add_binding(pattern, handler, settings)

    def add_plugin(self, handler, name, **settings):
        nid = settings.get('name') or name
        self.plugins[nid] = (handler, settings)

    def queue_message(self, callback, *args):
        self._queue.put_nowait((callback, args))

    def scan(self, module):
        self._scanner.scan(module)

    def start(self):
        spawns = [gevent.spawn(self._worker, n)
                  for n in xrange(self._workernum)]
        spawns.append(gevent.spawn(self.bot.start))
        self.running = True
        gevent.joinall(spawns)

    def _worker(self, n):
        while self.running:
            callback, args = self._queue.get()
            for handler, msg in self.dispatcher.get_matches(*args):
                try:
                    attr = msg.plugin_settings.get('attr')
                    if attr:
                        h = handler(msg)
                        res = getattr(h, attr)()
                    else:
                        res = handler(msg)
                    callback(res)
                except:
                    logger.exception("Error in executing plugin")
            gevent.sleep(0)


def irc_message_filter(settings, message):
    plugin_msgtypes = settings.get('msgtypes')
    plugin_targets = settings.get('targets')
    msgtypematch = (plugin_msgtypes is None or
                    message.msgtype in plugin_msgtypes)
    targetmatch = (plugin_targets is None or
                   message.target in plugin_targets)
    return msgtypematch and targetmatch

import re
import types
import logging
from collections import namedtuple


Message = namedtuple("Message", ['settings', 'type', 'metadata', 'message',
                                 'matchdict', 'plugin_settings'])


class MessageDispatcher:
    def __init__(self, settings=None, workers=4):
        self.settings = settings
        self.routes = []

    def add_binding(self, restr, handler, settings):
        self.routes.append((re_compile(restr), handler, settings))

    def msg(self, msgtype, message, metadata):
        for h, res, s in self._match_generator(msgtype, ' '.join(message)):
            d = res.groupdict()
            msg = Message(self.settings, msgtype, metadata, message, d, s)
            yield (h, msg)

    def _match_generator(self, msgtype, matchstr):
        for regex, handler, settings in self.routes:
            t = settings.get('msgtypes') or []
            if msgtype in t:
                res = regex.match(matchstr)
                if res:
                    yield handler, res, settings


def execute_handler(handler, msg):
    try:
        attr = msg.plugin_settings.get('attr')
        if attr:
            h = handler(msg)
            fun = getattr(h, attr, None)
            if isinstance(fun, types.MethodType):
                return fun()
        else:
            return handler(msg)
    except:
        logging.exception("Error in plugin")


def re_compile(restr):
    newstr = re.sub(r'{([^,\d}]+)}', r'(?P<\1>.+)', restr)
    return re.compile(newstr)

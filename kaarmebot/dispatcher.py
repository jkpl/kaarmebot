import re
import types
import logging
from collections import namedtuple


Message = namedtuple("Message", ['settings', 'matchdict', 'content',
                                 'plugin_settings'])


class MessageDispatcher:
    def __init__(self, settings=None, message_filter=lambda x, y: True):
        self.settings = settings
        self.message_filter = message_filter
        self.routes = []

    def add_binding(self, pattern, handler, settings):
        self.routes.append((re_compile(pattern), handler, settings))

    def msg(self, matchstr, messagedata):
        it = ((p, h, s) for p, h, s in self.routes
              if self.message_filter(s, messagedata))
        for pattern, handler, settings in it:
            res = pattern.match(matchstr)
            if res:
                d = res.groupdict()
                msg = Message(settings=self.settings, plugin_settings=settings,
                              matchdict=d, content=messagedata)
                yield (handler, msg)


def execute_handler(handler, msg):
    try:
        attr = msg.plugin_settings.get('attr')
        if attr:
            h = handler(msg)
            return getattr(h, attr)()
        else:
            return handler(msg)
    except:
        logging.exception("Error in plugin")


def re_compile(restr):
    newstr = re.sub(r'{([^,\d}]+)}', r'(?P<\1>.+)', restr)
    return re.compile(newstr)

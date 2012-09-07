import re
import types
from collections import namedtuple


Message = namedtuple("Message", ['settings', 'type', 'metadata',
                                 'message', 'matchdict'])


class MessageDispatcher:
    def __init__(self, settings=None):
        self.settings = settings
        self.routes = []

    def add_route(self, restr, msgtype, handler, attr=None):
        self.routes.append((re.compile(restr), msgtype, handler, attr))

    def msg(self, msgtype, message, metadata):
        for h, res, a in self._match_generator(msgtype, message):
            d = res.groupdict()
            if d:
                msg = Message(self.settings, msgtype, metadata, message, d)
                yield self.execute(h, a, msg)

    def execute(self, handler, attr, msg):
        if attr:
            h = handler(msg)
            fun = getattr(h, attr, None)
            if isinstance(fun, types.MethodType):
                return fun()
        else:
            res = handler(msg)
            return handler(msg)

    def _match_generator(self, msgtype, matchstr):
        for r, t, h, a in self.routes:
            if msgtype == t:
                res = r.match(matchstr)
                if res:
                    yield h, res, a

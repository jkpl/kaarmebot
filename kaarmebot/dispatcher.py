import re

class MessageDispatcher:
    def __init__(self):
        self.routes = []

    def add_route(self, restr, msgtype, handler):
        self.routes.append((re.compile(restr), msgtype, handler))

    def msg(self, msgtype, message, *metadata):
        for h, res in self._match_generator(msgtype, message):
            d = res.groupdict()
            t = res.groups()
            if d:
                yield h(*metadata, **d)
            else:
                yield h(*(metadata + t))

    def _match_generator(self, msgtype, matchstr):
        for r, t, h in self.routes:
            res = r.match(matchstr)
            if res and t == msgtype:
                yield h, res

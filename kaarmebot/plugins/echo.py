from irclib import nm_to_n

class Echo:
    def __init__(self, message):
        self.message = message

    def pubmsg(self):
        msg = self.message.matchdict.get('msg')
        target = self.message.metadata.get('target')
        if msg:
            return {'privmsg': ((target,'"%s"' % msg),)}
        return None


def echo_to_source(message):
    msg = message.matchdict.get('msg')
    target = message.metadata.get('target')
    source = nm_to_n(message.metadata.get('source'))
    if msg:
        return {'privmsg': ((target, "%s: %s" % (source, msg)),)}
    return None

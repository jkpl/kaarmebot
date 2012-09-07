from irclib import nm_to_n
from kaarmebot import plugin_config

class Echo:
    def __init__(self, message):
        self.message = message

    @plugin_config(name="echo1", msgtypes=("pubmsg",))
    def pubmsg(self):
        msg = self.message.matchdict.get('msg')
        nick = self.message.matchdict.get('nick')
        target = self.message.metadata.get('target')
        own_nick = self.message.metadata.get('own_nick')
        if msg and nick and nick == own_nick:
            return {'privmsg': ((target,'"%s"' % msg),)}
        return None


@plugin_config(name="echo2", msgtypes=("pubmsg", "privmsg"))
def echo_to_source(message):
    msg = message.matchdict.get('msg')
    nick = message.matchdict.get('nick')
    target = message.metadata.get('target')
    source = nm_to_n(message.metadata.get('source'))
    own_nick = message.metadata.get('own_nick')
    if msg and nick and nick == own_nick:
        if target != own_nick:
            return {'privmsg': ((target, "%s: %s" % (source, msg)),)}
        else:
            return {'privmsg': ((source, "%s: %s" % (source, msg)),)}
    return None

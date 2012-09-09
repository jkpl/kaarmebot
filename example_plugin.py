from irclib import nm_to_n
from kaarmebot import plugin_config
from urllib import urlopen
from urlparse import parse_qs
import re
import time
import json


class Echo:
    def __init__(self, message):
        self.msg = message.matchdict.get('msg')
        self.nick = message.matchdict.get('nick')
        self.target = message.content.target
        self.source = nm_to_n(message.content.source)
        self.own_nick = message.content.own_nick
        self.questionmarks = message.settings.get('questionmarks', 0)

    def add_questionmarks(self, msg):
        return msg + ('?' * self.questionmarks)

    @plugin_config(name="echo1", msgtypes=("pubmsg",))
    def pubmsg(self):
        if self.msg and self.nick and self.nick == self.own_nick:
            print '%s said "%s"' % (self.source, self.msg)
            time.sleep(6)  # do some blocking action
            msg = '"%s"' % self.add_questionmarks(self.msg)
            return {'privmsg': ((self.target, msg),)}
        return None


@plugin_config(name="echo2", msgtypes=("pubmsg", "privmsg"))
def echo_to_source(message):
    msg = message.matchdict.get('msg')
    nick = message.matchdict.get('nick')
    target = message.content.target
    source = nm_to_n(message.content.source)
    own_nick = message.content.own_nick
    if msg and nick and nick == own_nick:
        if target != own_nick:
            return {'privmsg': ((target, "%s: %s" % (source, msg)),)}
        else:
            return {'privmsg': ((source, "%s: %s" % (source, msg)),)}
    return None


@plugin_config(name="utube", msgtypes=("pubmsg",))
def utube(message):
    target = message.content.target
    vid = message.matchdict.get('vid')
    if vid is None:
        vid = parse_qs(message.matchdict.get('path', '')).get('v')[0]
    if vid:
        url = ''.join(('https://gdata.youtube.com/feeds/api/videos/',
                       vid, '?v=2&alt=json'))
        res = urlopen(url).read()
        d = json.loads(res)
        title = d['entry']['title']['$t']
        return {'privmsg': ((target, "YouTube: %s" % title),)}
    return None

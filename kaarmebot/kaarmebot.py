#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import types
import sys
import json
from botcore import BotCore
from dispatcher import MessageDispatcher


class KaarmeBot:
    def __init__(self, channels, servers, nickname, real_name,
                 plugin_settings, plugins):
        self.dispatcher = MessageDispatcher()
        self._init_plugins(plugins)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self.dispatcher.msg)

    def add_route(self, handler, pubmsg_regex=None, privmsg_regex=None,
                  pubmsg_attr=None, privmsg_attr=None):
        if pubmsg_regex:
            self.dispatcher.add_route(pubmsg_regex, 'pubmsg', handler,
                                      pubmsg_attr)
        if privmsg_regex:
            self.dispatcher.add_route(privmsg_regex, 'privmsg', handler,
                                      privmsg_attr)

    def _init_plugins(self, plugins):
        for pld in plugins:
            plfun = read_plugin(pld.get('plugin'))
            if plfun:
                pubre = pld.get('pub_re')
                privre = pld.get('priv_re')
                self.add_route(plfun, pubre, privre, pld.get('pub_attr'),
                               pld.get('priv_attr'))

    def start(self):
        self.bot.start()


def read_plugin(pluginstr):
    if isinstance(pluginstr, types.ClassType):
        return pluginstr
    elif isinstance(pluginstr, basestring):
        try:
            pluginpath = pluginstr.split('.')
            if len(pluginpath) > 1:
                mod = __import__('.'.join(pluginpath[:-1]))
                d = mod.__dict__
                for p in pluginpath[1:-1]:
                    d = d[p].__dict__
                return d[pluginpath[-1]]
            else:
                return globals()[pluginpath[0]]
        except (KeyError, ImportError, AttributeError) as e:
            print e
    return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cpath = sys.argv[1]
    else:
        cpath = "kaarmebot.json"
    conf = {}
    with open(cpath) as f:
        conf = json.loads(f.read())
    botcore = KaarmeBot(**conf)
    botcore.start()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import types
import sys
import json
from botcore import BotCore
from dispatcher import MessageDispatcher


class KaarmeBot:
    def __init__(self, channels, servers, nickname, real_name, plugins):
        self.dispatcher = MessageDispatcher()
        self._init_plugins(plugins)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self.dispatcher.msg)

    def _init_plugins(self, plugins):
        self.plugin_instances = []
        for pl in plugins:
            plugin_class = read_plugin(pl.get('plugin'))
            if plugin_class:
                pubre = pl.get('pub_re')
                privre = pl.get('priv_re')
                plsettings = pl.get('settings', {})
                plugin = plugin_class(plsettings)
                self.plugin_instances.append(plugin)
                if pubre:
                    self.dispatcher.add_route(pubre, 'pubmsg', plugin.pubmsg)
                if privre:
                    self.dispatcher.add_route(privre, 'privmsg',
                                              plugin.privmsg)

    def start(self):
        for pl in self.plugin_instances:
            if getattr(pl, 'setup', None):
                pl.setup()
        self.bot.start()

    def die(self):
        for pl in self.plugin_instances:
            if getattr(pl, 'teardown', None):
                pl.teardown()
        self.bot.die()


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

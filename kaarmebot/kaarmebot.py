#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import types
import sys
import json
from botcore import BotCore


class MessageDispatcher:
    def __init__(self, routes):
        self.routes = routes

    def msg(self, msgtype, message, *metadata):
        for h, res in self._match_generator(self.routes, msgtype, message):
            d = res.groupdict()
            t = res.groups()
            if d:
                yield h(*metadata, **d)
            else:
                yield h(*(metadata + t))

    def _match_generator(self, routes, msgtype, matchstr):
        for r, t, h in routes:
            res = r.match(matchstr)
            if res and t == msgtype:
                yield h, res


class KaarmeBot:
    def __init__(self, channels, servers, nickname, real_name, plugins):
        routes = self._init_plugins(plugins)
        self.dispatcher = MessageDispatcher(routes)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self.dispatcher.msg)

    def _init_plugins(self, plugins):
        self.plugin_instances = []
        routes = []
        for pl in plugins:
            plugin_class = read_plugin(pl.get('plugin', None))
            if plugin_class:
                pubre = pl.get('pub_re', None)
                privre = pl.get('priv_re', None)
                plsettings = pl.get('settings', {})
                plugin = plugin_class(plsettings)
                self.plugin_instances.append(plugin)
                if pubre:
                    routes.append((gen_route(pubre), 'pubmsg', plugin.pubmsg))
                if privre:
                    routes.append((gen_route(privre), 'privmsg', plugin.privmsg))
        return routes

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


def gen_route(restr):
    try:
        prog = re.compile(restr)
        return prog
    except Exception:
        print "Failed to compile, skipping:", route
    return None


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

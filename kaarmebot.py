#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import types
import sys
import json
from ircbot import SingleServerIRCBot


class BotCore(SingleServerIRCBot):
    def __init__(self, channels, servers, nickname, real_name, callbacks):
        SingleServerIRCBot.__init__(self, servers, nickname, real_name)
        self.channelset = set(channels)
        self.callbacks = callbacks

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for chan in self.channelset:
            c.join(chan)

    def on_pubmsg(self, c, e):
        target = e.target()
        source = e.source()
        args = e.arguments()[0].replace(c.get_nickname(), "{nick}")
        self._call_callback(c, 'pubmsg', target, source, args)

    def on_privmsg(self, c, e):
        source = e.source()
        args = e.arguments()[0]
        self._call_callback(c, 'privmsg', source, args)

    def _call_callback(self, connection, cbname, *args):
        cb = self.callbacks.get(cbname, None)
        if cb:
            for res in cb(*args):
                self.execute(connection, res)

    def execute(self, connection, d):
        if d:
            for k, v in d.iteritems():
                fun = getattr(connection, k, None)
                if (isinstance(fun, types.FunctionType) or
                    isinstance(fun, types.MethodType)):
                    fun(*v)

    def join(self, channel):
        self.channelset.add(channel)
        self.connection.join(channel)

    def part(self, channel, message=""):
        try:
            self.channelset.remove(channel)
            self.connection.part(channel, message)
        except KeyError:
            pass


class MessageDispatcher:
    def __init__(self, pub, priv):
        self.pubmsg_routes = pub
        self.privmsg_routes = priv

    def pubmsg(self, target, source, message):
        for h, res in self._match_generator(self.pubmsg_routes, message):
            d = res.groupdict()
            t = res.groups()
            if d:
                yield h(target, source, **d)
            else:
                yield h(target, source, *t)

    def privmsg(self, source, message):
        for h, res in self._match_generator(self.privmsg_routes, message):
            d = res.groupdict()
            t = res.groups()
            if d:
                yield h(source, **d)
            else:
                yield h(source, *t)

    def _match_generator(self, routes, matchstr):
        for r, h in routes:
            res = r.match(matchstr)
            if res:
                yield h, res


class KaarmeBot:
    def __init__(self, channels, servers, nickname, real_name, plugins):
        routes = self._init_plugins(plugins)
        self.dispatcher = MessageDispatcher(**routes)
        callbacks = {'pubmsg': self.dispatcher.pubmsg,
                     'privmsg': self.dispatcher.privmsg}
        self.bot = BotCore(channels, servers, nickname, real_name, callbacks)

    def _init_plugins(self, plugins):
        self.plugin_instances = []
        pub = []
        priv = []
        for pl in plugins:
            plugin_class = read_plugin(pl.get('plugin', None))
            if plugin_class:
                pubre = pl.get('pub_re', None)
                privre = pl.get('priv_re', None)
                plsettings = pl.get('settings', {})
                plugin = plugin_class(plsettings)
                self.plugin_instances.append(plugin)
                if pubre:
                    pub.append((gen_route(pubre), plugin.pubmsg))
                if privre:
                    priv.append((gen_route(privre), plugin.privmsg))
        return {'pub': pub, 'priv': priv}

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

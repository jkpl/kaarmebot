# -*- coding: utf-8 -*-

from ircbot import SingleServerIRCBot
import types


class BotCore(SingleServerIRCBot):
    def __init__(self, channels, servers, nickname, real_name, msgcallback):
        SingleServerIRCBot.__init__(self, servers, nickname, real_name)
        self.channelset = set(channels)
        self.msgcallback = msgcallback

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for chan in self.channelset:
            c.join(chan)

    def on_pubmsg(self, c, e):
        target = e.target()
        source = e.source()
        args = e.arguments()[0].replace(c.get_nickname(), "{nick}")
        self._call_callback(c, 'pubmsg', args, target=target, source=source)

    def on_privmsg(self, c, e):
        source = e.source()
        args = e.arguments()[0]
        self._call_callback(c, 'privmsg', args, target=target, source=source)

    def _call_callback(self, connection, msgtype, message, **metadata):
        for res in self.msgcallback(msgtype, message, metadata):
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

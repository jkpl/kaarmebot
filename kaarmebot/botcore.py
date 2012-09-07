# -*- coding: utf-8 -*-

from ircbot import SingleServerIRCBot
import types


class BotCore(SingleServerIRCBot):
    def __init__(self, channels, servers, nickname, real_name, msgcallback):
        SingleServerIRCBot.__init__(self, servers, nickname, real_name)
        self.channeld = channels
        self.msgcallback = msgcallback
        self.connection.add_global_handler("all_events",
                                           self._message_dispatch, -10)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        channels = self.channeld.get(c.server)
        if channels:
            for chan in channels:
                c.join(chan)

    def _message_dispatch(self, c, e):
        nick = c.get_nickname()
        target = e.target()
        source = e.source()
        args = [x.replace(nick, "{nick}") for x in e.arguments()]
        msgtype = e.eventtype()
        self._call_callback(c, msgtype, args, target=target, source=source,
                            own_nick=nick)

    def _call_callback(self, connection, msgtype, message, **metadata):
        for res in self.msgcallback(msgtype, message, metadata):
            if res:
                self.execute(connection, res)

    def execute(self, connection, d):
        for funname, arglist in d.iteritems():
            fun = getattr(connection, funname, None)
            if fun_or_method(fun):
                for args in arglist:
                    fun(*args)

    def join(self, channel):
        self.channelset.add(channel)
        self.connection.join(channel)

    def part(self, channel, message=""):
        try:
            self.channelset.remove(channel)
            self.connection.part(channel, message)
        except KeyError:
            pass

def fun_or_method(ob):
    return (isinstance(ob, types.FunctionType) or
            isinstance(ob, types.MethodType))
